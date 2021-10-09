from django.db import models
from django.core.validators import get_available_image_extensions
from .utils import compress_image
from django.core.exceptions import ValidationError

# Create your models here.
valid_image_extensions = get_available_image_extensions()

class CustomModel(models.Model):
    _image_compress_fields = []
    _notification_image_field_name = ''
    _is_data_fields_cleaned = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        image_fields = self._image_compress_fields
        if self._notification_image_field_name:
            image_fields = [*image_fields, self._notification_image_field_name]
        for f in image_fields:
            value = getattr(self, f) if hasattr(self, f) else None
            if not isinstance(value, (models.fields.files.ImageFieldFile, models.fields.files.FieldFile,)):
                raise AttributeError('{} is not a valid ImageField in {}'.format(f, self.__class__))
            setattr(self, '_original_{}_name'.format(f), value.name)

    def clean(self):
        super().clean()
        for f in self._image_compress_fields:
            value = getattr(self, f)
            if value and value.name.split('.')[-1].lower() not in valid_image_extensions:
                raise ValidationError({f: ['Invalid file format',]})
        if self._notification_image_field_name:
            value = getattr(self, self._notification_image_field_name)
            if value and getattr(self, '_original_{}_name'.format(self._notification_image_field_name)) != value.name:
                if value.name.split('.')[-1].lower() not in valid_image_extensions:
                    raise ValidationError({self._notification_image_field_name: ['Invalid file format',]})
                compressed_img = compress_image(value)
                if compressed_img and compressed_img.size <= 307200:
                    setattr(self, self._notification_image_field_name, compressed_img)
                else:
                    raise ValidationError({self._notification_image_field_name: ['Image size must be less than 300KB to send notification',]})
        self._is_data_fields_cleaned = True

    def save(self, exempt_compress = [], *args, **kwargs):
        for f in self._image_compress_fields:
            value = getattr(self, f)
            if value and getattr(self, '_original_{}_name'.format(f)) != value.name:
                if value.name.split('.')[-1].lower() not in valid_image_extensions:
                    raise TypeError('Invalid file format at {} field in {}'.format(f, self.__class__))
            if (f in exempt_compress or
                (f == self._notification_image_field_name and self._is_data_fields_cleaned)
            ):
                continue
            if value and getattr(self, '_original_{}_name'.format(f)) != value.name:
                # print('compressing ', value.name)
                setattr(self, f, compress_image(value))
        super().save(*args, **kwargs)

    class Meta:
        abstract = True


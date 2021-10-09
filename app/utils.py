from django.contrib.auth.hashers import make_password, check_password
from django.utils.baseconv import BaseConverter, BASE62_ALPHABET

# image compression import
import sys
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile

# def oneD_to_twoD(arr, row: int = None, col: int = None) -> list:
def oneD_to_twoD(arr, row = None, col = None):
    if row or col:
        n = len(arr)
        if row:
            col = n // row
            if n % row:
                col += 1
        return [arr[i:i + col] for i in range(0, n, col)]
    return arr

BASE64_ALPHABET = BASE62_ALPHABET + '+='

class HashBaseConverter(BaseConverter):
    def __init__(self, digits = BASE64_ALPHABET, sign = '-'):
        super().__init__(digits, sign = sign)
    
    def encode(self, decoded_value):
        if not decoded_value:
            return None
        try:
            decoded_value = str(decoded_value)
            base64_value = super().encode(decoded_value)
            encoded_value = make_password(decoded_value) + '$' + base64_value
            return encoded_value
        except Exception as e:
            pass
        return None
    
    def decode(self, encoded_value):
        if not encoded_value or '$' not in encoded_value:
            return None
        try:
            encoded_value = str(encoded_value).split('$')
            base10_value = str(super().decode(encoded_value[-1]))
            value_hash = '$'.join(encoded_value[:-1])
            if check_password(base10_value, value_hash):
                return base10_value
        except Exception as e:
            pass
        return None

hash_base_conv = HashBaseConverter()
from PIL.ExifTags import TAGS

def print_exif(image):
    exifdata = image.getexif()
    for tag_id in exifdata:
        # get the tag name, instead of human unreadable tag id
        tag = TAGS.get(tag_id, tag_id)
        data = exifdata.get(tag_id)
        # decode bytes 
        if isinstance(data, bytes):
            data = data.decode()
        print(f"{tag:25}: {data}")

def compress_image(file):
    temp = Image.open(file)
    out, img_format = None,''
    # print_exif(temp)
    if temp.mode not in ('RGBA', 'P',):
        try:
            out = BytesIO()
            img_format='jpeg'
            temp.save(out, format = 'JPEG', optimize = True, quality = 85)
        except Exception as e:
            out = None
    if out is None:
        out = BytesIO()
        img_format = 'png'
        temp.save(out, format = 'PNG', optimize = True, quality = 70)
    out.seek(0)
    file = InMemoryUploadedFile(out, 'ImageField', '{}.{}'.format(file.name.split('.')[0], img_format), 'image/{}'.format(img_format), sys.getsizeof(out), None)
    temp.close()
    return file


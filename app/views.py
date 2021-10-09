from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

# Create your views here.


class PaginateDetailsAPIView(APIView):
    ModelClass = None
    ModelSerializerClass = None
    serializer_fields = []
    filter_data = {}
    paginate_by = 10
    select_related_fields = []
    prefetch_related_fields = []
    show_count = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.ModelClass:
            raise ValueError('ModelClass field cannot be None')
        if not (self.ModelSerializerClass or self.serializer_fields):
            raise ValueError('Atleast one of serializer_fields or ModelSerializerClass must be specified')

    def get_filter_data(self, request, *args, **kwargs):
        return self.filter_data
    
    def get_model_class(self, request, *args, **kwargs):
        return self.ModelClass
    
    def get_serializer_class(self, request, *args, **kwargs):
        return self.ModelSerializerClass
    
    def get_queryset(self, request, *args, **kwargs):
        filter_data = self.get_filter_data(request, *args, **kwargs)
        model = self.get_model_class(request, *args, **kwargs)
        if filter_data is None:
            return model.objects.none()
        query = model.objects.filter(**filter_data)
        if self.select_related_fields:
            query = query.select_related(*self.select_related_fields)
        if self.prefetch_related_fields:
            query = query.prefetch_related(*self.prefetch_related_fields)
        return query

    def update_output(self, request, output):
        return output

    def get_last_value(self, obj):
        if obj:
            return str(obj.id)
        return None

    def paginate_query(self, request, query):
        last = request.GET.get('last', None)
        if last:
            query = query.filter(id__lt = last)
        query = query.order_by('-id')[:self.paginate_by]
        return query

    def get_serializer_context(self, request, *args, **kwargs):
        return {
            'request': request,
        }

    def get_serializer_fields(self, request, *args, **kwargs):
        return self.serializer_fields
    
    def get_serialized_output(self, request, query, *args, **kwargs):
        serializer_class = self.get_serializer_class(request, *args, **kwargs)
        if serializer_class:
            return serializer_class(query, many=True, context=self.get_serializer_context(request, *args, **kwargs)).data
        serializer_fields = self.get_serializer_fields(request, *args, **kwargs)
        if serializer_fields:
            try:
                out = list(query.values(*serializer_fields))
                return out
            except Exception as e:
                pass
        return list(query.values())

    def get_count_response(self, request, query, *args, **kwargs):
        return {
            'count': query.count(),
        }

    def get(self, request, *args, **kwargs):
        query = self.get_queryset(request, *args, **kwargs)
        count_res = {}
        if self.show_count and not request.GET.get('last',None):
            count_res = self.get_count_response(request, query, *args, **kwargs)
        query = self.paginate_query(request, query)

        last = None
        query_count = len(query)
        if query_count > 0 and query_count == self.paginate_by:
            last = self.get_last_value(query[query_count - 1])

        output_data = self.get_serialized_output(request, query, *args, **kwargs)
        output = {
            'status' : True,
            'detail': "succes",
            'data': output_data,
            'last': last,
            **count_res,
        }
        # import json
        # print(json.dumps(output, indent = 4))

        output = self.update_output(request, output)
        return Response(output, status=status.HTTP_200_OK, content_type="application/json")




class CreateUpdateDeleteView(APIView):
    model=None
    serializer=None
    def post(self, request, *args, **kwargs):
        user=request.user
        output_status=False
        output_detail="Falied"
        res_status=status.HTTP_400_BAD_REQUEST
        data={}
        extra_data={
            "user":user.id
        }
        serializer=self.serializer(data=request.data,extra_data=extra_data)
        if serializer.is_valid():
            serializer.save()
            output_status=True
            output_detail="Success"
            res_status=status.HTTP_200_OK
            data=serializer.data
        else:
            output_detail=serializer.errors
        context={
            "status":output_status,
            "detail":output_detail,
            "data":data
        }
        return Response(context, status=res_status)


    def delete(self, request, *args, **kwargs):
        user=request.user
        delete_data_id=request.GET.get("id")
        output_status=False
        output_detail="Falied"
        res_status=status.HTTP_400_BAD_REQUEST
        model=self.model.objects.filter(user=user,id=delete_data_id)
        if model:
            model.delete()
            output_status=True
            output_detail="Success"
            res_status=status.HTTP_400_BAD_REQUEST
        else:
            output_detail="you don't have access"
        context={
            "status":output_status,
            "detail":output_detail,
        }
        return Response(context, status=res_status)

    def put(self, request, *args, **kwargs):
        user=request.user
        update_data_id=request.data.get("id")
        output_status=False
        output_detail="Falied"
        res_status=status.HTTP_400_BAD_REQUEST
        data={}
        model=self.model.objects.filter(user=user,id=update_data_id).first()
        if model:
            serializer = self.serializer(model,data = request.data, partial = True)
            if serializer.is_valid():
                serializer.save()
                output_status=True
                output_detail="Data Updated"
                res_status=status.HTTP_400_BAD_REQUEST
                data=serializer.data
            else:
                output_detail=serializer.errors
        else:
            output_detail="you don't have access"
        context={
            "status":output_status,
            "detail":output_detail,
            "data":data
        }
        return Response(context, status=res_status)
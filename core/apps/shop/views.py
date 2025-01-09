from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.shop.models import Category
from apps.shop.serializers import CategorySerializer

tags = ["Shop"]


class CategoriesView(APIView):
    serializer_class = CategorySerializer

    @extend_schema(
        summary='Categories Fetch',
        description="""
            Эта конечная точка возвращает все категории.
        """,
        tags=tags
    )
    def get(self, request, *args, **kwargs):
        categories = Category.objects.all()
        serializer = self.serializer_class(categories, many=True)
        return Response(data=serializer.data, status=200)

    @extend_schema(
        summary='Category Create',
        description="""
            Эта конечная точка создает категории.
        """,
        tags=tags
    )
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            new_cat = Category.objects.create(**serializer.validated_data)
            serializer = self.serializer_class(new_cat)
            return Response(serializer.data, status=200)
        else:
            return Response(serializer.errors, status=400)

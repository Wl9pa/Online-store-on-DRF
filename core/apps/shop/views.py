from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.sellers.models import Seller
from apps.shop.models import Category, Product
from apps.shop.serializers import CategorySerializer, ProductSerializer

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


#  Этот код реализует простой эндпоинт для получения списка продуктов по slug категории.
#  Он включает в себя обработку ошибок (если категория не найдена) и оптимизированный запрос к базе данных.
class ProductsByCategoryView(APIView):
    serializer_class = ProductSerializer

    #  Параметр operation_id, который используется для уникальной идентификации операции API в спецификации OpenAPI
    @extend_schema(
        operation_id='category_products',
        summary='Category Products Fetch',
        description="""
            Эта конечная точка возвращает все продукты в определенной категории.
        """,
        tags=tags
    )
    def get(self, request, *args, **kwargs):
        category = Category.objects.get_or_none(slug=kwargs['slug'])
        if not category:
            return Response(data={'message': 'Category does not exist!'}, status=404)
        products = Product.objects.select_related('category', 'seller', 'seller__user').filter(category=category)
        serializer = self.serializer_class(products, many=True)
        return Response(data=serializer.data, status=200)


#  Представление, выводящие все товары интернет магазина
class ProductsView(APIView):
    serializer_class = ProductSerializer

    @extend_schema(
        operation_id='all_products',
        summary='Product Fetch',
        description="""
            Эта конечная точка возвращает все продукты.
        """,
        tags=tags
    )
    def get(self, request, *args, **kwargs):
        products = Product.objects.select_related('category', 'seller', 'seller__user').all()
        serializer = self.serializer_class(products, many=True)
        return Response(data=serializer.data, status=200)


#  Представление, выводящие все товары одного продавца, получая его slug
class ProductsBySellerView(APIView):
    serializer_class = ProductSerializer

    @extend_schema(
        summary='Seller Products Fetch',
        description="""
            Эта конечная точка возвращает все товары определенного продавца.
        """,
        tags=tags
    )
    def get(self, request, *args, **kwargs):
        seller = Seller.objects.get_or_none(slug=kwargs['slug'])
        if not seller:
            return Response(data={'message': 'Seller does not exist!'}, status=404)
        products = Product.objects.select_related('category', 'seller', 'seller__user').filter(seller=seller)
        serializer = self.serializer_class(products, many=True)
        return Response(data=serializer.data, status=200)


#  Представление вывода детальной информации о товаре, в нем мы получаем slug товара и выводим всю информацию о товаре
class ProductView(APIView):
    serializer_class = ProductSerializer

    def get_object(self, slug):
        product = Product.objects.get_or_none(slug=slug)
        return product

    @extend_schema(
        operation_id='product_detail',
        summary='Product Details Fetch',
        description="""
            Эта конечная точка возвращает информацию о продукте по его названию.
        """,
        tags=tags
    )
    def get(self, request, *args, **kwargs):
        product = self.get_object(kwargs['slug'])
        if not product:
            return Response(data={'message': 'Product does not exist!'}, status=404)
        serializer = self.serializer_class(product)
        return Response(data=serializer.data, status=200)

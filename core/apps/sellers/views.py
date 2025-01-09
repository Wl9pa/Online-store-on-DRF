from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.utils import set_dict_attr
from apps.sellers.models import Seller
from apps.sellers.serializers import SellerSerializer
from apps.shop.models import Product, Category
from apps.shop.serializers import ProductSerializer, CreateProductSerializer

tags = ['Sellers']


#  представление APIView, обрабатывающее POST-запросы для создания или обновления профиля продавца (Seller)
class SellersView(APIView):
    serializer_class = SellerSerializer

    @extend_schema(
        summary='Apply to become a seller',
        description="""
            Эта конечная точка позволяет покупателю подать заявку на то, чтобы стать продавцом.
        """,
        tags=tags
    )
    def post(self, request):
        user = request.user
        serializer = self.serializer_class(data=request.data, partial=False)
        if serializer.is_valid():
            data = serializer.validated_data
            seller, _ = Seller.objects.update_or_create(user=user, defaults=data)
            user.account_type = 'SELLER'
            user.save()
            serializer = self.serializer_class(seller)
            return Response(data=serializer.data, status=201)
            #  Этот подход обеспечивает идемпотентность — повторные вызовы с теми же данными не создадут дубликаты.
        else:
            return Response(data=serializer.error, status=400)


class ProductsBySellerView(APIView):
    serializer_class = ProductSerializer

    @extend_schema(
        summary='Seller Products Fetch',
        description="""
            Эта конечная точка возвращает все товары продавца.
            Продукты можно отфильтровать по названию, размерам или цветам.
        """,
        tags=tags
    )
    def get(self, request, *args, **kwargs):
        seller = Seller.objects.get_or_none(user=request.user, is_approved=True)
        if not seller:
            return Response(data={'message': 'Access is denied'}, status=403)
        products = Product.objects.select_related('category', 'seller', 'seller__user').filter(seller=seller)
        serializer = self.serializer_class(products, many=True)
        return Response(data=serializer.data, status=200)

    @extend_schema(
        summary='Create a product',
        description="""
            Эта конечная точка позволяет продавцу создать продукт.
        """,
        tags=tags,
        request=CreateProductSerializer,
        responses=CreateProductSerializer,
    )  # сериализаторы для запроса и ответа, это сделано для того,
       # чтобы корректно предустанавливать текст запроса и ответа в Swagger.
    def post(self, request, *args, **kwargs):
        serializer = CreateProductSerializer(data=request.data)
        seller = Seller.objects.get_or_none(user=request.user, is_approved=True)
        if not seller:
            return Response(data={'message': 'Access is denied'}, status=403)
        if serializer.is_valid():
            data = serializer.validated_data
            category_slug = data.pop('category_slug', None)  # получаем введенный slug категории
            # и удаляем его из сериализованных данных.
            category = Category.objects.get_or_none(slug=category_slug)  # Находим категорию по slug
            if not category:
                return Response(data={'message': 'Category does not exist!'}, status=404)
            data['category'] = category
            data['seller'] = seller
            #  Добавляем данные о категории и продавце в данные для создания продукта.
            new_prod = Product.objects.create(**data)  # Создаем новый продукт с помощью полученных данных.
            serializer = self.serializer_class(new_prod)  # Сериализуем созданный продукт для возврата клиенту.
            return Response(serializer.data, status=200)
        else:
            return Response(serializer.errors, status=400)


class SellerProductView(APIView):
    serializer_class = CreateProductSerializer

    def get_object(self, slug):
        product = Product.objects.get_or_none(slug=slug)
        return product

    @extend_schema(
        summary='Seller Products Update',
        description="""
            Эта конечная точка обновляет продукт продавца.
        """,
        tags=tags
    )
    def put(self, request, *args, **kwargs):
        product = self.get_object(kwargs['slug'])
        if not product:
            return Response(data={'message': 'Product does not exist!'}, status=404)
        #  Это критически важная проверка. Она гарантирует, что только продавец может его изменить.
        elif product.seller != request.user.seller:
            return Response(data={'message': 'Access is denied'}, status=403)
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            category_slug = data.pop('category_slug', None)
            category = Category.objects.get_or_none(slug=category_slug)
            if not category:
                return Response(data={'message': 'Category does not exist!'}, status=404)
            data['category'] = category
            if data['price_current'] != product.price_current:
                data['price_old'] = product.price_current
            product = set_dict_attr(product, data)
            product.save()
            serializer = ProductSerializer(product)
            return Response(data=serializer.data, status=200)
        else:
            return Response(data=serializer.errors, status=400)


    def delete(self, request, *args, **kwargs):
        product = self.get_object(kwargs['slug'])
        if not product:
            return Response(data={'message': 'Product does not exist!'}, status=404)
        elif product.seller != request.user.seller:
            return Response(data={'message': 'Access is denied'}, status=403)
        product.delete()
        return Response(data={'message': 'Product deleted successfully'}, status=200)

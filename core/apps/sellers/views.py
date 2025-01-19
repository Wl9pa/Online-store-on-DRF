from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.permissions import IsSeller
from apps.common.utils import set_dict_attr
from apps.profiles.models import Order, OrderItem
from apps.sellers.models import Seller
from apps.sellers.serializers import SellerSerializer
from apps.shop.models import Product, Category
from apps.shop.serializers import ProductSerializer, CreateProductSerializer, OrderSerializer, CheckItemOrderSerializer

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
        #  Получает объект текущего авторизованного пользователя из запроса
        user = request.user
        #  Создает экземпляр сериализатора SellerSerializer, используя данные из тела запроса (request.data).
        #  partial=False означает, что все поля в сериализаторе обязательны для заполнения.
        serializer = self.serializer_class(data=request.data, partial=False)
        if serializer.is_valid():
            #  Извлекает валидированные данные из сериализатора.
            #  Это словарь, содержащий данные, готовые для сохранения в базе данных.
            data = serializer.validated_data
            #  update_or_create — метод менеджера моделей Django.
            #  Он пытается найти запись в таблице Seller, где user совпадает с текущим пользователем.
            #  Если такая запись найдена, она обновляется с использованием значений из defaults(то есть, data).
            seller, _ = Seller.objects.update_or_create(user=user, defaults=data)
            #  Мы меняем тип аккаунта пользователя, с покупателя на продавца.
            user.account_type = 'SELLER'
            user.save()
            #  Создает новый экземпляр сериализатора, используя полученный или созданный объект seller.
            serializer = self.serializer_class(seller)
            return Response(data=serializer.data, status=201)
            #  Этот подход обеспечивает идемпотентность — повторные вызовы с теми же данными не создадут дубликаты.
        else:
            return Response(data=serializer.error, status=400)


class ProductsBySellerView(APIView):
    permission_classes = [IsSeller]
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
    permission_classes = [IsSeller]
    serializer_class = CreateProductSerializer

    #  Вспомогательный метод, который получает продукт из базы данных по его slug.
    #  Он использует get_or_none, что предотвращает ошибки, если товар не найден.
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
        product = self.get_object(kwargs['slug'])  # Получаем продукт по slug из URL.
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
            #  Eсли текущая цена изменилась, старая цена сохраняется в поле price_old.
            if data['price_current'] != product.price_current:
                data['price_old'] = product.price_current
            # Это вызов функции set_dict_attr. Она обновляет атрибуты объекта product с помощью данных из сериализатора.
            product = set_dict_attr(product, data)
            product.save()
            serializer = ProductSerializer(product)
            return Response(data=serializer.data, status=200)
        else:
            return Response(data=serializer.errors, status=400)

    @extend_schema(
        summary="Seller Product Delete",
        description="""
                Эта конечная точка позволяет продавцу удалить продукт.
            """,
        tags=tags
    )
    def delete(self, request, *args, **kwargs):
        product = self.get_object(kwargs['slug'])
        if not product:
            return Response(data={'message': 'Product does not exist!'}, status=404)
        elif product.seller != request.user.seller:
            return Response(data={'message': 'Access is denied'}, status=403)
        product.delete()
        return Response(data={'message': 'Product deleted successfully'}, status=200)


#  будет показывать список всех заказов, где продавец участвовал в качестве продавца хотя бы одного товара в заказе.
class SellerOrdersView(APIView):
    permission_classes = [IsSeller]
    serializer_class = OrderSerializer

    @extend_schema(
        operation_id='seller_orders',
        summary='Seller Orders Fetch',
        description="""
            Эта конечная точка возвращает все заказы для определенного продавца.
        """,
        tags=tags
    )
    def get(self, request):
        #  Получает объект продавца из текущего авторизованного пользователя.
        #  Предполагается, что модель пользователя имеет отношение seller.
        seller = request.user.seller
        #  Выполняет запрос к базе данных для получения всех заказов, где хотя бы один элемент заказа (orderitems)
        #  содержит продукт (product), принадлежащий текущему продавцу (seller).
        #  Заказы сортируются по дате создания в обратном порядке (-created_at).
        orders = (Order.objects.filter(orderitems__product__seller=seller).order_by('-created_at'))
        #  Создается сериализатор для сериализации списка заказов.
        serializer = self.serializer_class(orders, many=True)
        #  Возвращает HTTP-ответ с кодом 200 (OK) и сериализованными данными заказов.
        return Response(data=serializer.data, status=200)


#  возвращает список элементов заказов (товаров) для конкретного заказа, принадлежащего данному продавцу
class SellerOrderItemView(APIView):
    permission_classes = [IsSeller]
    serializer_class = CheckItemOrderSerializer

    @extend_schema(
        operation_id='seller_orders_items_view',
        summary='Seller Item Orders Fetch',
        description="""
            Эта конечная точка возвращает все заказы на товары для определенного продавца.
        """,
        tags=tags
    )
    def get(self, request, **kwargs):
        #  Получение объекта продавца.
        seller = request.user.seller
        #  Получение заказа по tx_ref (идентификатор транзакции), передаваемому в параметрах URL.
        #  get_or_none возвращает None, если заказ не найден.
        order = Order.objects.get_or_none(tx_ref=kwargs['tx_ref'])
        if not order:
            return Response(data={'message': 'Order does not exist!'}, status=404)
        #  Получение элементов заказа, учитывая, что они принадлежат найденному заказу и продавцу.
        order_items = OrderItem.objects.filter(order=order, product__seller=seller)
        #  Сериализация элементов заказа.
        serializer = self.serializer_class(order_items, many=True)
        #  Возврат ответа
        return Response(data=serializer.data, status=200)

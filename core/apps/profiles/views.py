from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.utils import set_dict_attr
from apps.profiles.models import ShippingAddress, Order, OrderItem

from apps.profiles.serializers import ProfileSerializer, ShippingAddressSerializer
from apps.shop.serializers import OrderSerializer, CheckItemOrderSerializer

tags = ['Profiles']


class ProfileView(APIView):
    serializer_class = ProfileSerializer

    @extend_schema(
        summary='Retrieve Profile',
        description="""
            Эта конечная точка позволяет пользователю получить свой профиль.
        """,
        tags=tags,
    )
    def get(self, request):
        user = request.user
        serializer = self.serializer_class(user)
        return Response(data=serializer.data, status=200)

    @extend_schema(
        summary='Update Profile',
        description="""
            Эта конечная точка позволяет пользователю обновить свой профиль.
        """,
        tags=tags,
        request={'multipart/form-data': serializer_class}
    )
    def put(self, request):
        user = request.user
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = set_dict_attr(user, serializer.validated_data)
        user.save()
        serializer = self.serializer_class(user)
        return Response(data=serializer.data)

    @extend_schema(
        summary='Deactivate account',
        description="""
            Эта конечная точка позволяет пользователю деактивировать свою учетную запись.
        """,
        tags=tags,
    )
    def delete(self, request):
        user = request.user
        user.is_active = False
        user.save()
        return Response(data={'message': 'Учетная запись пользователя деактивирована'})


class ShippingAddressView(APIView):
    serializer_class = ShippingAddressSerializer

    @extend_schema(
        summary='Shipping Addresses Fetch',
        description="""
            Эта конечная точка возвращает все адреса доставки, связанные с пользователем.
        """,
        tags=tags,
    )
    def get(self, request, *args, **kwargs):
        user = request.user
        shipping_addresses = ShippingAddress.objects.filter(user=user)
        serializer = self.serializer_class(shipping_addresses, many=True)
        return Response(data=serializer.data)

    @extend_schema(
        summary='Create Shipping Address',
        description="""
            Эта конечная точка позволяет пользователю создать адрес доставки.
        """,
        tags=tags
    )
    def post(self, request, *args, **kwargs):
        user = request.user
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        shipping_address, _ = ShippingAddress.objects.get_or_create(user=user, **data)  # _ используется
        # для игнорирования возвращаемого значения bool, указывающего, был ли создан новый объект или нет
        # Нам это не нужно. Мы используем эту логику, в случае если пользователь не изменяет свой адрес доставки
        # но отправляет POST запрос, мы его получали из БД, а не записывали еще раз в БД.
        serializer = self.serializer_class(shipping_address)
        return Response(data=serializer.data, status=201)


class ShippingAddressViewID(APIView):
    serializer_class = ShippingAddressSerializer

    #  Это вспомогательный метод, который получает адрес доставки из базы данных по ID.
    #  Он использует метод get_or_none для возврата объекта или None, если id не найден.
    def get_object(self, user, shipping_id):
        shipping_address = ShippingAddress.objects.get_or_none(id=shipping_id)
        return shipping_address

    @extend_schema(
        summary="Shipping Address Fetch ID",
        description="""
            Эта конечная точка возвращает один адрес доставки, связанный с пользователем.
        """,
        tags=tags,
    )
    def get(self, request, *args, **kwargs):
        user = request.user
        shipping_address = self.get_object(user, kwargs['id'])
        if not shipping_address:
            return Response(data={'message': 'Адреса доставки не существует!'})
        serializer = self.serializer_class(shipping_address)
        return Response(data=serializer.data)

    @extend_schema(
        summary="Update Shipping Address ID",
        description="""
            Эта конечная точка позволяет пользователю обновить свой адрес доставки.
        """,
        tags=tags,
    )
    def put(self, request, *args, **kwargs):
        user = request.user
        shipping_address = self.get_object(user, kwargs['id'])
        if not shipping_address:
            return Response(data={'message': 'Адреса доставки не существует!'}, status=404)
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        shipping_address = set_dict_attr(shipping_address)
        shipping_address.save()
        serializer = self.serializer_class(shipping_address)
        return Response(data=serializer.data, status=200)

    @extend_schema(
        summary="Delete Shipping Address ID",
        description="""
            Эта конечная точка позволяет пользователю удалить свой адрес доставки.
        """,
        tags=tags,
    )
    def delete(self, request, *args, **kwargs):
        user = request.user
        shipping_address = self.get_object(user, kwargs['id'])
        if not shipping_address:
            return Response(data={'message': 'Адреса доставки не существует!'}, status=404)
        shipping_address.delete()
        return Response(data={'message': 'Адрес доставки успешно удален'}, status=200)


#  Это представление возвращает список всех заказов, принадлежащих конкретному пользователю.
class OrdersView(APIView):
    serializer_class = OrderSerializer

    @extend_schema(
        operation_id='orders_view',
        summary='Orders Fetch',
        description="""
            Эта конечная точка возвращает все заказы для конкретного пользователя.
        """,
        tags=tags
    )
    def get(self, request, *args, **kwargs):
        #  Получает объект текущего авторизованного пользователя.
        user = request.user
        #  Выполняет запрос к базе данных для получения заказов текущего пользователя.
        #  .select_related("user"): Загружает связанную модель пользователя (user) для каждого заказа
        #  чтобы избежать дополнительных запросов к базе данных.
        #  .prefetch_related("orderitems", "orderitems__product"): Предварительно загружает связанные элементы заказа
        #  (orderitems) и продукты внутри этих элементов (orderitems__product).
        #  .order_by("-created_at"): Сортирует заказы по полю created_at в обратном порядке (от самых новых к старым).
        orders = (Order.objects.filter(user=user).select_related('user')
                  .prefetch_related('orderitems', 'orderitems__product')
                  .order_by('-created_at'))
        #  Создается сериализатор для сериализации списка заказов.
        serializer = self.serializer_class(orders, many=True)
        #  Возвращает HTTP-ответ с кодом 200 (OK) и сериализованными данными заказов.
        return Response(data=serializer.data, status=200)


#  Это представление возвращает список элементов конкретного заказа (товаров внутри заказа).
class OrderItemView(APIView):
    serializer_class = CheckItemOrderSerializer

    @extend_schema(
        operation_id='orders_items_view',
        summary='Item Orders Fetch',
        description="""
            Эта конечная точка возвращает все заказы на товары для конкретного пользователя.
        """,
        tags=tags
    )
    def get(self, request, *args, **kwargs):
        #  Получаем заказ по tx_ref (идентификатор транзакции), передаваемому в параметрах URL.
        #  get_or_none возвращает None, если заказ не найден.
        order = Order.objects.get_or_none(tx_ref=kwargs['tx_ref'])
        if not order or order.user != request.user:
            return Response(data={'message': 'Order does not exist!'}, status=404)
        #  Получаем товары заказа, принадлежащих к найденному заказу.
        order_items = OrderItem.objects.filter(order=order)
        #  Сериализация элементов заказа.
        serializer = self.serializer_class(order_items, many=True)
        #  Возврат ответа.
        return Response(data=serializer.data, status=200)

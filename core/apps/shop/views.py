from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.profiles.models import OrderItem, ShippingAddress, Order
from apps.sellers.models import Seller
from apps.shop.models import Category, Product
from apps.shop.serializers import CategorySerializer, ProductSerializer, OrderItemSerializer, ToggleCartItemSerializer

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


class CartView(APIView):
    serializer_class = OrderItemSerializer

    @extend_schema(
        summary='Cart Items Fetch',
        description="""
            Эта конечная точка возвращает все товары в пользовательской корзине.
        """,
        tags=tags
    )
    def get(self, request, *args, **kwargs):
        # Получаем текущего авторизованного пользователя.
        user = request.user
        #  Получаем все элементы корзины текущего пользователя (order=None проверяем на то,
        #  что товары находятся в корзине, а не в оформленном заказе). select_related используем
        #  для оптимизации запроса, загружая связанные данные о продукте, продавце и пользователе продавца.
        orderitems = OrderItem.objects.filter(user=user, order=None).select_related(
            'product', 'product__seller', 'product__seller__user')
        #  Сериализуем полученные элементы корзины.
        serializer = self.serializer_class(orderitems, many=True)
        #   Возвращаем сериализованные данные.
        return Response(data=serializer.data)

    @extend_schema(
        summary='Toggle Item in cart',
        description="""
            Эта конечная точка позволяет пользователю или гостю добавить/обновить/удалить товар в корзине.
            Если количество равно 0, товар удаляется из корзины
        """,
        tags=tags,
        request=ToggleCartItemSerializer
    )
    def post(self, request, *args, **kwargs):  # POST-запрос (добавление, обновление или удаление товара из корзины).
        #  Получает объект пользователя из текущего запроса (предполагается аутентификация).
        user = request.user
        #  Создает экземпляр сериализатора ToggleCartItemSerializer с данными из тела запроса.
        serializer = ToggleCartItemSerializer(data=request.data)
        #  Валидирует данные. Если валидация не пройдена, будет возбуждено исключение.
        serializer.is_valid(raise_exception=True)
        #  Получает валидированные данные из сериализатора.
        data = serializer.validated_data
        #  Извлекает количество товара из валидированных данных.
        quantity = data['quantity']
        #  Получает продукт из базы данных по его slug.
        #  get_or_none возвращает None, если продукт не найден, избегая исключений.
        product = Product.objects.select_related('seller', 'seller__user').get_or_none(slug=data['slug'])
        #  Проверка на существование продукта. Если продукт не найден, возвращает ошибку 404.
        if not product:
            return Response({'message': 'No Product with that slug'}, status=404)
        #  Попытка обновить существующую запись OrderItem или создать новую.
        orderitem, created = OrderItem.objects.update_or_create(
            user=user,  # Пользователь, которому принадлежит товар.
            order_id=None,  # Указывает, что товар находится в корзине (а не в оформленном заказе).
            product=product,  # Товар, который нужно добавить/обновить.
            #  Если запись обновляется, поле quantity будет обновлено значением из запроса.
            #  Это ключевой момент: функция update_or_create обновляет только указанные поля в defaults.
            defaults={'quantity': quantity},
        )
        resp_message_substring = 'Updated In'  # Инициализация переменной для формирования сообщения ответа.
        status_code = 200  # Инициализация кода статуса.
        #  Если был создан новый OrderItem, код статуса меняется на 201 (Created), и сообщение изменяется на “Added To”.
        if created:
            status_code = 201
            resp_message_substring = 'Added To'
        #  Если количество равно 0, товар удаляется из корзины, и сообщение изменяется на “Removed From”.
        if orderitem.quantity == 0:
            resp_message_substring = 'Removed From'
            orderitem.delete()  # Удаление записи из базы данных.
        data = None  # Сбрасывает переменную data.
        #  Если товар не был удален, сериализует обновленный OrderItem и сохраняет данные в переменной data.
        if resp_message_substring != 'Removed From':
            orderitem.product = product
            serializer = self.serializer_class(orderitem)
            data = serializer.data
        #  Возвращает ответ с сообщением и данными о товаре (если товар не был удален).
        return Response(data={'message': f"Item {resp_message_substring} Cart", 'item': data}, status=status_code)

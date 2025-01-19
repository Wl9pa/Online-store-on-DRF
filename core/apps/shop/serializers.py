from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.profiles.serializers import ShippingAddressSerializer
from apps.sellers.serializers import SellerSerializer
from apps.shop.models import Review


class CategorySerializer(serializers.Serializer):
    name = serializers.CharField()
    slug = serializers.SlugField(read_only=True)
    image = serializers.ImageField()


#  Этот сериализатор используется для сериализации данных о продавце (магазине).
class SellerShopSerializer(serializers.Serializer):
    name = serializers.CharField(source='business_name')  # Строковое поле для имени продавца
    # получаемое из поля business_name модели продавца.
    slug = serializers.CharField()
    avatar = serializers.CharField(source='user.avatar')  # Строковое поле для аватара продавца
    # получаемое из поля avatar модели пользователя
    # связанного с продавцом (user.avatar).


#  Этот сериализатор предназначен для сериализации данных о продукте.
#  Он использует вложенные сериализаторы для продавца и категории.
class ProductSerializer(serializers.Serializer):
    seller = SellerShopSerializer()  # Вложенный сериализатор для данных о продавце.
    name = serializers.CharField()
    slug = serializers.SlugField()
    desc = serializers.CharField()
    price_old = serializers.DecimalField(max_digits=10, decimal_places=2)
    price_current = serializers.DecimalField(max_digits=10, decimal_places=2)
    category = CategorySerializer()
    in_stock = serializers.IntegerField()
    image1 = serializers.ImageField()
    image2 = serializers.ImageField(required=False)
    image3 = serializers.ImageField(required=False)


#  Этот сериализатор, похожий на ProductSerializer, но предназначен для создания продукта.
#  Он не использует вложенных сериализаторов для продавца и категории
#  а использует category_slug — slug категории передается напрямую.
class CreateProductSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    desc = serializers.CharField()
    price_current = serializers.DecimalField(max_digits=10, decimal_places=2)
    category_slug = serializers.CharField()
    in_stock = serializers.IntegerField()
    image1 = serializers.ImageField()
    image2 = serializers.ImageField(required=False)
    image3 = serializers.ImageField(required=False)


#  Этот сериализатор используется для представления информации о продукте внутри элемента заказа
#  (то есть, товара в корзине). Он не сериализует всю модель Product, а только необходимые поля.
class OrderItemProductSerializer(serializers.Serializer):
    seller = SellerSerializer()
    name = serializers.CharField()
    slug = serializers.SlugField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2, source='price_current')


#  Этот сериализатор используется для представления всего элемента заказа (то есть, записи в корзине).
class OrderItemSerializer(serializers.Serializer):
    product = OrderItemProductSerializer()
    quantity = serializers.IntegerField()
    total = serializers.FloatField(source='get_total')


#  Этот сериализатор используется для валидации данных, отправленных клиентом при добавлении,
#  обновлении или удалении товара из корзины. Он не сериализует данные модели OrderItem целиком,
#  а только те поля, которые необходимы для этой операции. Получая идентификатор продукта (slug) и количество товара.
class ToggleCartItemSerializer(serializers.Serializer):
    slug = serializers.SlugField()
    quantity = serializers.IntegerField(min_value=0)


#   Сериализатор для валидации данных, связанных с этапом оформления заказа до создания самого заказа.
class CheckoutSerializer(serializers.Serializer):
    #  Это поле представляет собой идентификатор (UUID) информации о доставке, которое пользователь уже сохранил ранее.
    shipping_id = serializers.UUIDField()


#  Сериализатор предназначен для представления данных о заказе после его создания.
#  Он включает в себя информацию о пользователе, статусе доставки и оплаты, стоимости и других деталях.
class OrderSerializer(serializers.Serializer):
    #  Уникальный идентификатор транзакции (можем использовать для формирования запроса оплаты).
    tx_ref = serializers.CharField()
    #  Имя пользователя.
    first_name = serializers.CharField(source='user.first_name')
    #  Фамилия пользователя.
    last_name = serializers.CharField(source='user.last_name')
    #  Email пользователя.
    email = serializers.EmailField(source='user.email')
    #  Статус доставки заказа.
    delivery_status = serializers.CharField()
    #  Статус оплаты заказа.
    payment_status = serializers.CharField()
    #  Дата и время доставки заказа.
    date_delivered = serializers.DateTimeField()
    #  Детали доставки. SerializerMethodField указывает
    #  что данные для этого поля будут получены из метода get_shipping_details.
    shipping_details = serializers.SerializerMethodField()
    #  Итоговая стоимость товаров в заказе (например без учета доставки).
    #  source="get_cart_subtotal" указывает на метод модели Order, который вычисляет эту сумму
    subtotal = serializers.DecimalField(max_digits=100, decimal_places=2, source='get_cart_subtotal')
    #  Общая стоимость заказа (с учетом доставки). source="get_cart_total" аналогично subtotal
    total = serializers.DecimalField(max_digits=100, decimal_places=2, source='get_cart_total')

    #  Этот метод используется для получения данных о доставке. Он использует ShippingAddressSerializer
    #  для сериализации данных об адресе доставки и возвращает сериализованные данные.
    #  Здесь  @extend_schema_field(ShippingAddressSerializer) указывает
    #  что возвращаемый тип данных соответствует сериализатору ShippingAddressSerializer.
    @extend_schema_field(ShippingAddressSerializer)
    def get_shipping_details(self, obj):
        return ShippingAddressSerializer(obj).data


class ItemProductSerializer(serializers.Serializer):
    name = serializers.CharField()
    slug = serializers.SlugField()
    desc = serializers.CharField()
    price_old = serializers.DecimalField(max_digits=10, decimal_places=2)
    price_current = serializers.DecimalField(max_digits=10, decimal_places=2)
    category = CategorySerializer()
    image1 = serializers.ImageField()
    image2 = serializers.ImageField(required=False)
    image3 = serializers.ImageField(required=False)


#  Это сериализатор для представления позиции в заказе.
#  В сущности, CheckItemOrderSerializer использует ItemProductSerializer для вложенного представления
#  товара в позиции заказа. total вычисляется динамически (умножением quantity на price_current).
class CheckItemOrderSerializer(serializers.Serializer):
    #  вложенный сериализатор ItemProductSerializer для представления товара
    product = ItemProductSerializer()
    #  целое число, количество товара
    quantity = serializers.IntegerField()
    #  число с плавающей точкой, общая стоимость позиции; вычисляется методом  get_total модели OrderItem
    total = serializers.FloatField(source='get_total')


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['id', 'rating', 'text']
        read_only_fields = ['id']

    def validate(self, data):
        user = self.context['request'].user
        product_slug = self.context['view'].kwargs.get('product_slug')

        existing_review = Review.objects.filter(
            user=user,
            product__slug=product_slug,
            is_deleted=False
        ).first()

        if existing_review:
            raise serializers.ValidationError('Вы уже оставили отзыв на этот продукт')

        return data

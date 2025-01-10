from rest_framework import serializers

from apps.sellers.serializers import SellerSerializer


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

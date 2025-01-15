import django_filters

from apps.shop.models import Product


class ProductFilter(django_filters.FilterSet):
    #  Фильтрует продукты с ценой (price_current) меньше или равной значению max_price, переданному в запросе.
    #  lookup_expr='lte' определяет оператор сравнения (“меньше либо равно”).
    max_price = django_filters.NumberFilter(field_name='price_current', lookup_expr='lte')
    #  Тоже самое, что и max_price, но указывает минимальный порог
    min_price = django_filters.NumberFilter(field_name='price_current', lookup_expr='gte')
    #  Фильтрует продукты с количеством на складе (in_stock) больше или равным значению in_stock, переданному в запросе.
    #  Поле in_stock в модели — это числовое поле, представляющее количество товаров на складе.
    #  lookup_expr='gte' используется для фильтрации по количеству, большему или равному указанному.
    in_stock = django_filters.NumberFilter(lookup_expr='gte')
    #  Фильтрует продукты, дата создания которых (created_at) больше или равна значению created_at,
    #  переданному в запросе.  lookup_expr='gte' определяет оператор сравнения.
    created_at = django_filters.DateTimeFilter(lookup_expr='gte')

    #  метаданные для FilterSet
    class Meta:
        #  Указывает модель, к которой применяются фильтры.
        model = Product
        #  Указывает поля, по которым можно фильтровать. Этот список определяет, какие фильтры будут доступны.
        fields = ['max_price', 'min_price', 'in_stock', 'created_at']


#  Пользователь сможет фильтровать продукты, указывая параметры в URL-запросе:
#
# shop/products/?max_price=100: Продукты с ценой не больше 100.
# shop/products/?min_price=50&max_price=100: Продукты с ценой от 50 до 100.
# shop/products/?in_stock=10: Продукты с количеством на складе 10 и более.
# shop/products/?created_at=2024-01-01: Продукты, созданные 1 января 2024 года и позже.

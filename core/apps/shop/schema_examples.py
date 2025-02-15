from drf_spectacular.utils import OpenApiParameter, OpenApiTypes
from core import settings


PRODUCT_PARAM_EXAMPLE = [
    OpenApiParameter(
        name='max_price',
        description='Фильтр товаров по текущей цене MAX',
        required=False,
        type=OpenApiTypes.INT,
    ),
    OpenApiParameter(
        name='min_price',
        description='Фильтр товаров по текущей цене MIN',
        required=False,
        type=OpenApiTypes.INT,
    ),
    OpenApiParameter(
        name='in_stock',
        description='Фильтр товаров по наличию',
        required=False,
        type=OpenApiTypes.INT,
    ),
    OpenApiParameter(
        name='created_at',
        description='Фильтр продуктов по дате создания',
        required=False,
        type=OpenApiTypes.DATE,
    ),
    OpenApiParameter(
        name='page',
        description='Получение определенной страницы. По умолчанию 1',
        required=False,
        type=OpenApiTypes.INT,
    ),
    OpenApiParameter(
        name='page_size',
        description=f"Количество элементов на странице, которое вы хотите отобразить."
                    f"По умолчанию {settings.REST_FRAMEWORK['PAGE_SIZE']}",
        required=False,
        type=OpenApiTypes.INT,
    ),
]

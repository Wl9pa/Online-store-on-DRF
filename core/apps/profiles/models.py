from django.db import models

from apps.accounts.models import User
from apps.common.models import BaseModel
from apps.common.utils import generate_unique_code
from apps.shop.models import Product

DELIVERY_STATUS_CHOICES = (
    ("PENDING", "PENDING"),
    ("PACKING", "PACKING"),
    ("SHIPPING", "SHIPPING"),
    ("ARRIVING", "ARRIVING"),
    ("SUCCESS", "SUCCESS"),
)

PAYMENT_STATUS_CHOICES = (
    ("PENDING", "PENDING"),
    ("PROCESSING", "PROCESSING"),
    ("SUCCESSFUL", "SUCCESSFUL"),
    ("CANCELLED", "CANCELLED"),
    ("FAILED", "FAILED"),
)


class ShippingAddress(BaseModel):
    """
    Представляет адрес доставки, связанный с пользователем.

    Атрибуты:
        user (ForeignKey): Пользователь, которому принадлежит адрес доставки.
        full_name (str): Полное имя получателя.
        email (str): Адрес электронной почты получателя.
        phone (str): Номер телефона получателя.
        адрес (str): Уличный адрес получателя.
        город (str): Город получателя.
        страна (str): Страна получателя.
        zipcode (int): Почтовый индекс получателя.

    Методы:
        __str__():
            Возвращает строковое представление данных о доставке.
    """

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='shipping_addresses'
    )
    full_name = models.CharField(max_length=1000)
    email = models.EmailField()
    phone = models.CharField(max_length=20, null=True)
    address = models.CharField(max_length=1000, null=True)
    city = models.CharField(max_length=200, null=True)
    country = models.CharField(max_length=200, null=True)
    zipcode = models.IntegerField(null=True)

    def __str__(self):
        return f"{self.full_name}'s shipping details"


class Order(BaseModel):
    """
    Представляет заказ клиента.

    Атрибуты:
        user (ForeignKey): Пользователь, разместивший заказ.
        tx_ref (str): Уникальная ссылка на транзакцию.
        delivery_status (str): Статус доставки заказа.
        payment_status (str): Статус оплаты заказа.

    Методы:
        __str__():
            Возвращает строковое представление ссылки на транзакцию.
        save(*args, **kwargs):
            Переопределяет метод save для генерации уникальной ссылки на транзакцию при создании нового заказа.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    tx_ref = models.CharField(max_length=100, blank=True, unique=True)
    delivery_status = models.CharField(
        max_length=20, default='PENDING', choices=DELIVERY_STATUS_CHOICES
    )
    payment_status = models.CharField(
        max_length=20, default='PENDING', choices=PAYMENT_STATUS_CHOICES
    )
    date_delivered = models.DateTimeField(null=True, blank=True)

    #  Данные об адресе доставки
    full_name = models.CharField(max_length=1000, null=True)
    email = models.EmailField(null=True)
    phone = models.CharField(max_length=20, null=True)
    address = models.CharField(max_length=1000, null=True)
    city = models.CharField(max_length=100, null=True)
    zipcode = models.IntegerField(null=True)

    def __str__(self):
        return f"{self.user.full_name}'s order"

    def save(self, *args, **kwargs) -> None:
        if self._state.adding:
            self.tx_ref = generate_unique_code(Order, "tx_ref")
        super().save(*args, **kwargs)


class OrderItem(BaseModel):
    """
    Представляет элемент в заказе.

    Атрибуты:
        order (ForeignKey): Заказ, к которому относится данный товар.
        product (ForeignKey): Товар, связанный с этой позицией заказа.
        quantity (int): Количество заказанного продукта.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    order = models.ForeignKey(
        Order,
        related_name='orderitems',
        null=True,
        on_delete=models.CASCADE,
        blank=True,
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    @property
    def get_total(self):
        return self.product.price_current * self.quantity

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return str(self.product.name)

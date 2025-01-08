from django.contrib.auth.models import AbstractBaseUser
from django.db import models
from django.utils import timezone

from apps.accounts.managers import CustomUserManager
from apps.common.models import IsDeletedModel
from core import settings

ACCOUNT_TYPE_CHOICES = (
    ('SELLER', 'SELLER'),
    ('BUYER', 'BUYER')
)


class User(AbstractBaseUser, IsDeletedModel):
    """
    Пользовательская модель пользователя, расширяющая AbstractBaseUser.
    Атрибуты:
        first_name (str): Первое имя пользователя.
        last_name (str): Фамилия пользователя.
        email (str): Адрес электронной почты пользователя, используемый в качестве поля имени пользователя.
        avatar (ImageField): Изображение аватара пользователя.
        is_staff (bool): Указывает, может ли пользователь войти на этот административный сайт.
        is_active (bool): Указывает, следует ли считать этого пользователя активным.
        account_type (str): Тип учетной записи (ПРОДАВЕЦ или ПОКУПАТЕЛЬ).
    Методы:
        full_name(): Возвращает полное имя пользователя.
        __str__(): Возвращает строковое представление пользователя.
    """

    first_name = models.CharField(verbose_name='First name', max_length=25, null=True)
    last_name = models.CharField(verbose_name='Last name', max_length=25, null=True)
    email = models.EmailField(verbose_name='Email address', unique=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, default='avatars/default.jpg')

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    account_type = models.CharField(max_length=6, choices=ACCOUNT_TYPE_CHOICES, default='BUYER')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = CustomUserManager()

    @property
    def full_name(self):
        """
        Возвращает полное имя пользователя, объединяя имя и фамилию.

        Возвращает:
            str: Полное имя пользователя.
        """
        return f'{self.first_name} {self.last_name}'

    def __str__(self):
        """
        Возвращает строковое представление пользователя, которое является его полным именем.

        Возвращает:
            str: Полное имя пользователя.
        """
        return self.full_name

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    @property
    def is_superuser(self):
        return self.is_staff

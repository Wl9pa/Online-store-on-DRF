import uuid
from django.db import models
from django.utils import timezone

from apps.common.managers import GetOrNoneManager, IsDeletedManager


class BaseModel(models.Model):
    """
    Базовый класс модели, который включает в себя общие поля и методы для всех моделей.

    Атрибуты:
        id (UUIDField): Уникальный идентификатор для экземпляра модели.
        created_at (DateTimeField): Временная метка, когда был создан экземпляр.
        updated_at (DateTimeField): Временная метка последнего обновления экземпляра.
    """
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = GetOrNoneManager()

    class Meta:
        abstract = True


class IsDeletedModel(BaseModel):
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    objects = IsDeletedManager()

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])

    def hard_delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)

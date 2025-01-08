import secrets

from apps.common.models import BaseModel


def generate_unique_code(model: BaseModel, field: str) -> str:
    """
    Генерирует уникальный код для указанной модели и поля.

    Args:
        model (BaseModel): Класс модели для проверки на уникальность.
        field (str): Имя поля, которое нужно проверить на уникальность.

    Возвращает:
        str: Уникальный код.
    """

    allowed_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ123456789"
    unique_code = "".join(secrets.choice(allowed_chars) for _ in range(12))
    code = unique_code
    similar_object_exists = model.objects.filter(**{field: code}).exists()
    if not similar_object_exists:
        return code
    return generate_unique_code(model, field)


#  set_dict_attr позволяет обновлять атрибуты объекта динамически, используя данные из словаря
#  если количество атрибутов, которые нужно обновить, неизвестно заранее или меняется.
#  Вместо множественного присваивания user.attr1 = ..., user.attr2 = ... и т.д., используется один вызов set_dict_attr
def set_dict_attr(obj, data):
    for attr, value in data.items():
        setattr(obj, attr, value)  # Или obj.attr = value для каждого атрибута
    return obj

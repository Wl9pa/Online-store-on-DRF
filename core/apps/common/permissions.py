from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    #  Этот метод проверяет, имеет ли пользователь право доступа к представлению в целом.
    #  Он вызывается перед тем, как DRF попытается получить доступ к конкретному объекту.
    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return True
        return False

    #  Этот метод проверяет, имеет ли пользователь право доступа к конкретному объекту.
    #  Он вызывается после has_permission и только если has_permission вернул True.
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user or request.user.is_staff


class IsSeller(permissions.BasePermission):
    def has_permission(self, request, view):
        if (request.user.is_authenticated and request.user.account_type == 'SELLER') or request.user.is_staff:
            return True
        return False

    def has_object_permission(self, request, view, obj):
        return obj.seller == request.user.seller or request.user.is_staff

from rest_framework.permissions import (IsAuthenticatedOrReadOnly,
                                        IsAdminUser, SAFE_METHODS)


class AdminOnlyPermission(IsAuthenticatedOrReadOnly):
    """Небезопасные методы доступны только администратору."""

    message = 'Изменять сообщества может только администратор.'

    def has_permission(self, request, view):
        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            return IsAdminUser().has_permission(request, view)
        return True


class IsAuthorOrReadOnly(IsAuthenticatedOrReadOnly):
    """Изменять контент может только его автор."""

    message = 'Изменять контент может только его автор.'

    def has_object_permission(self, request, view, obj):
        return request.method in SAFE_METHODS or obj.author == request.user
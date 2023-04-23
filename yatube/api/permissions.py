from rest_framework.permissions import (IsAuthenticatedOrReadOnly,
                                        IsAdminUser, SAFE_METHODS,
                                        IsAuthenticated)


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


class IsAuthenticatedAuthor(IsAuthenticated):
    """Доступ имеет только аутентифицированный пользователь.
    Получать и изменять информацию о подписках может только подписчик."""

    message = 'Управлять подпиской может только подписчик.'

    def has_object_permission(self, request, view, obj):
        return request.method in SAFE_METHODS or obj.user == request.user
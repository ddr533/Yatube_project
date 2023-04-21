from rest_framework.permissions import BasePermission, IsAdminUser


class AdminOnlyPermission(BasePermission):
    """
    Небезопасные методы доступны только администратору.
    """
    def has_permission(self, request, view):
        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            return IsAdminUser().has_permission(request, view)
        return True
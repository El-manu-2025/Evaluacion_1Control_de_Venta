from rest_framework.permissions import BasePermission


class IsAdminUserGroup(BasePermission):
    """Permite acceso solo a usuarios en el grupo 'Admin'."""

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return user.groups.filter(name='Admin').exists() or user.is_superuser


class IsClientUser(BasePermission):
    """Permite acceso a usuarios autenticados que no son Admin."""

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return not (user.groups.filter(name='Admin').exists() or user.is_superuser)

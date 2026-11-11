"""DRF permission adapters for product administration capabilities."""
from rest_framework.permissions import BasePermission

from Usuarios.permissions import can_access_backoffice, is_platform_admin


class IsSystemAdmin(BasePermission):
    def has_permission(self, request, view):
        return can_access_backoffice(request.user)


class IsPlatformAdmin(BasePermission):
    def has_permission(self, request, view):
        return is_platform_admin(request.user)

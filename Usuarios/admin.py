from django.contrib import admin
from .models import AuditEvent


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'actor', 'action', 'resource_type', 'resource_id', 'outcome', 'request_id')
    readonly_fields = ('timestamp', 'actor', 'action', 'resource_type', 'resource_id', 'outcome', 'request_id')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
from .models import Perfil
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken


class ProtectedUserAdmin(UserAdmin):
    def has_delete_permission(self, request, obj=None):
        return False


admin.site.unregister(User)
admin.site.register(User, ProtectedUserAdmin)
# Default token admins expose stored token material or allow undoing revocation.
# Revocation is handled by authentication flows, not generic admin CRUD.
admin.site.unregister(OutstandingToken)
admin.site.unregister(BlacklistedToken)

@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ('user', 'telefono', 'direccion')
    search_fields = ('user__username', 'user__email', 'telefono')

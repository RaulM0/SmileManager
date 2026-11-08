from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

from Usuarios.models import AuditEvent
from api.policies import can_access_backoffice, has_backoffice_assignment, has_platform_assignment


class AdministrativeAccountProtected(Exception):
    pass


@transaction.atomic
def create_user(*, actor, username, email, first_name, last_name, password, backoffice_access, request_id):
    if not can_access_backoffice(actor):
        raise PermissionDenied
    user = get_user_model().objects.create_user(
        username=username, email=email, first_name=first_name, last_name=last_name, password=password,
    )
    AuditEvent.objects.create(actor=actor, action='USER_CREATED', resource_type='user',
                              resource_id=str(user.pk), outcome='success', request_id=request_id)
    if backoffice_access:
        permission = Permission.objects.get(content_type__app_label='Usuarios', codename='access_system_backoffice')
        user.user_permissions.add(permission)
        AuditEvent.objects.create(actor=actor, action='BACKOFFICE_ACCESS_GRANTED', resource_type='user',
                                  resource_id=str(user.pk), outcome='success', request_id=request_id)
    return user


def set_user_active(*, actor, user_id, active, request_id):
    if not can_access_backoffice(actor):
        raise PermissionDenied
    with transaction.atomic():
        user = get_object_or_404(get_user_model().objects.select_for_update(), pk=user_id)
        if user.pk == actor.pk or user.is_staff or user.is_superuser or has_backoffice_assignment(user) or has_platform_assignment(user):
            raise AdministrativeAccountProtected
        if user.is_active != active:
            user.is_active = active
            user.save(update_fields=['is_active'])
            if not active:
                for token in OutstandingToken.objects.select_for_update().filter(user=user, expires_at__gt=timezone.now()).iterator():
                    BlacklistedToken.objects.get_or_create(token=token)
            AuditEvent.objects.create(actor=actor, action='USER_ACTIVATED' if active else 'USER_DEACTIVATED', resource_type='user', resource_id=str(user.pk), outcome='success', request_id=request_id)
        return user

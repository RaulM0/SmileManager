"""Explicit product administration assignments, independent of HTTP views."""

def has_backoffice_assignment(user):
    # Django's has_perm grants everything to superusers. This product
    # capability instead requires an explicit direct or group assignment.
    from django.contrib.auth.models import Permission
    from django.db.models import Q
    return Permission.objects.filter(content_type__app_label='Usuarios', codename='access_system_backoffice').filter(Q(user=user) | Q(group__user=user)).exists()


def has_platform_assignment(user):
    from Usuarios.models import PlatformAdmin
    return bool(user and user.is_authenticated and PlatformAdmin.objects.filter(user_id=user.pk, is_active=True).exists())


def is_platform_admin(user):
    return bool(user and user.is_authenticated and user.is_active and has_platform_assignment(user))


def can_access_backoffice(user):
    return bool(user and user.is_authenticated and user.is_active and (has_backoffice_assignment(user) or is_platform_admin(user)))

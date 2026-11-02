"""Ámbito único actual: propietario del paciente y relaciones coherentes."""
from django.db.models import F, Q
from django.shortcuts import get_object_or_404
from rest_framework.permissions import BasePermission

from Citas.models import Cita
from Pacientes.models import (AntescedentesMedicos, Consentimiento, Consulta,
                             EstudioComparativo, ImagenesClinicas, Odontograma, Paciente)


def scoped(user, model):
    """Nunca amplía acceso para staff; admin usa sus propios permisos."""
    if not user.is_authenticated or not user.is_active:
        return model.objects.none()
    if model is Paciente:
        return model.objects.filter(medico_id=user.pk)
    if model is Cita:
        return model.objects.filter(paciente__medico_id=user.pk)
    if model not in (AntescedentesMedicos, Consentimiento, Consulta, EstudioComparativo, ImagenesClinicas, Odontograma):
        raise ValueError('Modelo sin política de autorización')
    queryset = model.objects.filter(paciente__medico_id=user.pk, medico_id=user.pk)
    if model is ImagenesClinicas:
        queryset = queryset.filter(Q(consulta__isnull=True) | Q(consulta__paciente_id=F('paciente_id'), consulta__medico_id=user.pk))
    return queryset


def owned_or_404(user, model, **lookup):
    return get_object_or_404(scoped(user, model), **lookup)


def consistent_or_404(user, model, patient):
    """No ignorar silenciosamente registros ajenos asociados al paciente."""
    from django.http import Http404
    all_rows = model.objects.filter(paciente=patient)
    if all_rows.exclude(pk__in=scoped(user, model).values('pk')).exists():
        raise Http404
    return scoped(user, model).filter(paciente=patient)


def has_backoffice_assignment(user):
    # Django's has_perm grants everything to superusers. This product
    # capability instead requires an explicit direct or group assignment.
    from django.contrib.auth.models import Permission
    from django.db.models import Q
    return Permission.objects.filter(content_type__app_label='Usuarios', codename='access_system_backoffice').filter(Q(user=user) | Q(group__user=user)).exists()


def can_access_backoffice(user):
    return bool(user and user.is_authenticated and user.is_active and has_backoffice_assignment(user))


class IsSystemAdmin(BasePermission):
    def has_permission(self, request, view):
        return can_access_backoffice(request.user)

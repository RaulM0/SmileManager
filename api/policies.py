"""Ámbito único actual: propietario del paciente y relaciones coherentes."""
from django.db.models import Exists, F, Q
from django.shortcuts import get_object_or_404
from rest_framework.permissions import BasePermission

from Citas.models import Cita
from Pacientes.models import (AntescedentesMedicos, Consentimiento, Consulta,
                             EstudioComparativo, ImagenesClinicas, Odontograma, Paciente)


def _doctor_scoped(user, model):
    """Existing professional assignment rule, before tenant filtering."""
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
        queryset = queryset.filter(is_active=True).filter(Q(consulta__isnull=True) | Q(consulta__paciente_id=F('paciente_id'), consulta__medico_id=user.pk))
    return queryset


def scoped(user, model):
    """Legacy access is restricted to unassigned data and users without memberships.

    Tenant-aware services must use clinic_clinical_queryset instead. This guard
    prevents the old routes from becoming a bypass when a user or patient has
    entered the tenant migration; historical data is not assigned implicitly.
    """
    from Usuarios.models import ClinicMembership

    queryset = _doctor_scoped(user, model)
    if not user.is_authenticated or not user.is_active:
        return queryset
    prefix = 'clinic' if model is Paciente else 'paciente__clinic'
    memberships = ClinicMembership.objects.filter(user_id=user.pk)
    return queryset.filter(**{f'{prefix}__isnull': True}).alias(
        _legacy_has_membership=Exists(memberships),
    ).filter(_legacy_has_membership=False)


def clinic_clinical_queryset(user, clinic_id, model):
    """Clinical access requires a live doctor membership and patient assignment.

    This policy is not yet wired into legacy routes. Callers must also use
    validated tenant context for writes and enforce relational consistency.
    """
    from api.tenant_context import require_clinic_capability
    from Usuarios.models import Clinic, ClinicMembership

    membership = require_clinic_capability(user, clinic_id, 'clinical.assigned')
    queryset = _doctor_scoped(user, model)
    prefix = 'clinic' if model is Paciente else 'paciente__clinic'
    return queryset.filter(**{
        f'{prefix}__id': membership.clinic_id,
        f'{prefix}__status': Clinic.Status.ACTIVE,
        f'{prefix}__memberships__user_id': user.pk,
        f'{prefix}__memberships__user__is_active': True,
        f'{prefix}__memberships__status': ClinicMembership.Status.ACTIVE,
        f'{prefix}__memberships__role': ClinicMembership.Role.DOCTOR,
    })


def owned_or_404(user, model, **lookup):
    return get_object_or_404(scoped(user, model), **lookup)


def consistent_or_404(user, model, patient, clinic_id=None):
    """No ignorar silenciosamente registros ajenos asociados al paciente."""
    from django.http import Http404
    all_rows = model.objects.filter(paciente=patient)
    authorized = clinic_clinical_queryset(user, clinic_id, model) if clinic_id is not None else scoped(user, model)
    if all_rows.exclude(pk__in=authorized.values('pk')).exists():
        raise Http404
    return authorized.filter(paciente=patient)


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


class IsSystemAdmin(BasePermission):
    def has_permission(self, request, view):
        return can_access_backoffice(request.user)


class IsPlatformAdmin(BasePermission):
    def has_permission(self, request, view):
        return is_platform_admin(request.user)

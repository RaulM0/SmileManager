"""Ámbito único actual: propietario del paciente y relaciones coherentes."""
from django.db.models import Exists, F, Q
from django.conf import settings
from django.shortcuts import get_object_or_404

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

    if not settings.LEGACY_CLINICAL_API_ENABLED:
        return model.objects.none()
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

    Callers must also use validated tenant context for writes and enforce
    relational consistency. Retired routes cannot grant tenant access.
    """
    from Usuarios.clinic_context import require_clinic_capability
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

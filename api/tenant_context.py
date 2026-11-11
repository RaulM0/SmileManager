"""Live clinic membership and capability boundaries for organizational APIs."""
from uuid import UUID

from django.contrib.auth import get_user_model
from django.db import connection
from rest_framework.exceptions import PermissionDenied

from Usuarios.models import Clinic, ClinicMembership


# These capabilities are deliberately coarse. A clinical capability never
# replaces the separate professional-to-patient authorization check.
ROLE_CAPABILITIES = {
    ClinicMembership.Role.CLINIC_ADMIN: frozenset({'clinic.manage', 'membership.manage', 'clinic.audit'}),
    ClinicMembership.Role.DOCTOR: frozenset({'clinical.assigned'}),
    ClinicMembership.Role.STAFF: frozenset({'appointments.manage'}),
}


def resolve_clinic_membership(user, clinic_id):
    """Resolve a requested clinic afresh; indistinguishable failures disclose no membership."""
    if not user or not user.is_authenticated or not user.is_active:
        raise PermissionDenied('Contexto de clínica no autorizado.')
    try:
        clinic_id = UUID(str(clinic_id))
    except (ValueError, TypeError, AttributeError):
        raise PermissionDenied('Contexto de clínica no autorizado.')
    membership = ClinicMembership.objects.select_related('clinic').filter(
        user_id=user.pk, clinic_id=clinic_id, status=ClinicMembership.Status.ACTIVE,
        clinic__status=Clinic.Status.ACTIVE,
    ).first()
    if membership is None:
        raise PermissionDenied('Contexto de clínica no autorizado.')
    return membership


def require_clinic_capability(user, clinic_id, capability):
    """Revalidate live membership; callers must additionally enforce resource policy."""
    membership = resolve_clinic_membership(user, clinic_id)
    if capability not in ROLE_CAPABILITIES.get(membership.role, frozenset()):
        raise PermissionDenied('Operación no autorizada.')
    return membership


def lock_clinic_capability(user, clinic_id, capability):
    """Revalidate under the common clinic-then-user lock order inside a transaction."""
    if not connection.in_atomic_block:
        raise RuntimeError('Tenant write or administrative read requires a transaction.')
    try:
        clinic_id = UUID(str(clinic_id))
    except (ValueError, TypeError, AttributeError):
        raise PermissionDenied('Contexto de clínica no autorizado.') from None
    clinic = Clinic.objects.select_for_update().filter(pk=clinic_id).first()
    account = get_user_model().objects.select_for_update().filter(pk=user.pk, is_active=True).first()
    if clinic is None or account is None:
        raise PermissionDenied('Contexto de clínica no autorizado.')
    return require_clinic_capability(account, clinic.pk, capability)

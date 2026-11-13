"""Clinic membership administration; no invitation or clinical access is granted here."""
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import APIException, PermissionDenied, ValidationError

from Usuarios.models import AuditEvent, Clinic, ClinicMembership


class MembershipConflict(APIException):
    status_code = 409
    default_detail = 'La operación no está permitida para el estado actual de la membresía.'


@transaction.atomic
def change_membership(*, actor, clinic_id, membership_id, role, status, request_id):
    # All membership mutations in this service serialize on the clinic first.
    clinic = get_object_or_404(Clinic.objects.select_for_update(), pk=clinic_id)
    actor_membership = ClinicMembership.objects.filter(
        clinic=clinic, user_id=actor.pk, user__is_active=True,
        status=ClinicMembership.Status.ACTIVE, role=ClinicMembership.Role.CLINIC_ADMIN,
    ).first()
    if clinic.status != Clinic.Status.ACTIVE or actor_membership is None:
        raise PermissionDenied('Operación no autorizada.')
    target = get_object_or_404(ClinicMembership.objects.select_for_update(), clinic=clinic, pk=membership_id)
    new_role = role if role is not None else target.role
    new_status = status if status is not None else target.status
    if new_role not in ClinicMembership.Role.values or new_status not in ClinicMembership.Status.values:
        raise ValidationError('Rol o estado no válido.')
    # Revocation terminates membership; a fresh acceptance flow is needed to return.
    if target.status == ClinicMembership.Status.REVOKED and (new_status != target.status or new_role != target.role):
        raise MembershipConflict('Una membresía revocada requiere una nueva invitación aceptada.')
    if target.status != ClinicMembership.Status.ACTIVE and new_status == ClinicMembership.Status.ACTIVE and target.joined_at is None:
        raise MembershipConflict('La membresía requiere una invitación aceptada.')
    was_admin = target.status == ClinicMembership.Status.ACTIVE and target.role == ClinicMembership.Role.CLINIC_ADMIN and target.user.is_active
    remains_admin = new_status == ClinicMembership.Status.ACTIVE and new_role == ClinicMembership.Role.CLINIC_ADMIN and target.user.is_active
    if was_admin and not remains_admin and not ClinicMembership.objects.filter(
        clinic=clinic, status=ClinicMembership.Status.ACTIVE,
        role=ClinicMembership.Role.CLINIC_ADMIN, user__is_active=True,
    ).exclude(pk=target.pk).exists():
        raise MembershipConflict('La clínica debe conservar un administrador activo.')
    if target.role != new_role or target.status != new_status:
        target.role, target.status = new_role, new_status
        target.save(update_fields=['role', 'status', 'updated_at'])
        AuditEvent.objects.create(clinic=clinic, actor=actor, action='CLINIC_MEMBERSHIP_CHANGED',
                                  resource_type='clinic_membership', resource_id=str(target.pk),
                                  request_id=request_id)
    return target

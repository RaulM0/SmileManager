"""Explicitly authorized platform onboarding and clinic state transitions."""
import secrets
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from Usuarios.models import AuditEvent, Clinic, ClinicInvitation, ClinicMembership, PlatformAdmin
from api.policies import is_platform_admin
from .clinics import transition_clinic
from .invitations import _digest
from .memberships import MembershipConflict


def _locked_platform_actor(actor):
    account = get_user_model().objects.select_for_update().filter(pk=actor.pk, is_active=True).first()
    role = PlatformAdmin.objects.select_for_update().filter(user_id=actor.pk, is_active=True).first()
    if account is None or role is None:
        raise PermissionDenied('Operación no autorizada.')
    return account


def _initial_invitation(*, clinic, actor, email, request_id):
    email = email.strip().casefold()
    try:
        validate_email(email)
    except DjangoValidationError as exc:
        raise ValidationError({'email': 'Correo no válido.'}) from exc
    if len(email) > 254:
        raise ValidationError({'email': 'Correo no válido.'})
    if ClinicMembership.objects.filter(clinic=clinic, role=ClinicMembership.Role.CLINIC_ADMIN,
                                       status=ClinicMembership.Status.ACTIVE, user__is_active=True).exists():
        raise MembershipConflict('La clínica ya tiene un administrador activo.')
    now = timezone.now()
    pending = ClinicInvitation.objects.filter(clinic=clinic, role=ClinicMembership.Role.CLINIC_ADMIN,
                                              status=ClinicInvitation.Status.PENDING)
    pending.filter(expires_at__lte=now).update(status=ClinicInvitation.Status.REVOKED, resolved_at=now)
    if pending.exists():
        raise MembershipConflict('Ya existe una invitación de administración pendiente.')
    token = secrets.token_urlsafe(32)
    invitation = ClinicInvitation.objects.create(clinic=clinic, email=email,
                                                 role=ClinicMembership.Role.CLINIC_ADMIN,
                                                 token_hash=_digest(token), invited_by=actor,
                                                 expires_at=now + timedelta(days=7))
    AuditEvent.objects.create(clinic=clinic, actor=actor, action='PLATFORM_INITIAL_ADMIN_INVITED',
                              resource_type='clinic_invitation', resource_id=str(invitation.pk), request_id=request_id)
    return invitation, token


@transaction.atomic
def create_clinic(*, actor, name, slug, status, initial_admin_email, request_id):
    if not is_platform_admin(actor):
        raise PermissionDenied('Operación no autorizada.')
    actor = _locked_platform_actor(actor)
    if status not in (Clinic.Status.ACTIVE, Clinic.Status.INACTIVE):
        raise ValueError('Estado inicial no válido.')
    clinic = Clinic(name=name, slug=slug, status=status)
    try:
        clinic.full_clean(validate_unique=False, validate_constraints=False)
    except DjangoValidationError as exc:
        raise ValidationError(exc.message_dict) from exc
    clinic.save()
    AuditEvent.objects.create(clinic=clinic, actor=actor, action='PLATFORM_CLINIC_CREATED',
                              resource_type='clinic', resource_id=str(clinic.pk), request_id=request_id)
    invitation, token = _initial_invitation(clinic=clinic, actor=actor, email=initial_admin_email, request_id=request_id)
    return clinic, invitation, token


@transaction.atomic
def change_clinic_status(*, actor, clinic_id, target, request_id):
    if not is_platform_admin(actor):
        raise PermissionDenied('Operación no autorizada.')
    clinic = get_object_or_404(Clinic.objects.select_for_update(), pk=clinic_id)
    actor = _locked_platform_actor(actor)
    old_status = clinic.status
    clinic = transition_clinic(clinic_id=clinic.pk, target=target)
    if clinic.status != old_status:
        AuditEvent.objects.create(clinic=clinic, actor=actor, action=f'PLATFORM_CLINIC_{clinic.status}',
                                  resource_type='clinic', resource_id=str(clinic.pk), request_id=request_id)
    return clinic


@transaction.atomic
def change_clinic_ai(*, actor, clinic_id, enabled, request_id):
    if not is_platform_admin(actor):
        raise PermissionDenied('Operación no autorizada.')
    clinic = get_object_or_404(Clinic.objects.select_for_update(), pk=clinic_id)
    actor = _locked_platform_actor(actor)
    if clinic.ai_enabled != enabled:
        clinic.ai_enabled = enabled
        clinic.save(update_fields=['ai_enabled', 'updated_at'])
        AuditEvent.objects.create(
            clinic=clinic,
            actor=actor,
            action='PLATFORM_CLINIC_AI_ENABLED' if enabled else 'PLATFORM_CLINIC_AI_DISABLED',
            resource_type='clinic',
            resource_id=str(clinic.pk),
            request_id=request_id,
        )
    return clinic


@transaction.atomic
def invite_initial_administrator(*, actor, clinic_id, email, request_id):
    if not is_platform_admin(actor):
        raise PermissionDenied('Operación no autorizada.')
    clinic = get_object_or_404(Clinic.objects.select_for_update(), pk=clinic_id)
    actor = _locked_platform_actor(actor)
    return _initial_invitation(clinic=clinic, actor=actor, email=email, request_id=request_id)


@transaction.atomic
def revoke_initial_invitation(*, actor, clinic_id, invitation_id, request_id):
    if not is_platform_admin(actor):
        raise PermissionDenied('Operación no autorizada.')
    clinic = get_object_or_404(Clinic.objects.select_for_update(), pk=clinic_id)
    actor = _locked_platform_actor(actor)
    invitation = get_object_or_404(ClinicInvitation.objects.select_for_update(), clinic=clinic,
                                   pk=invitation_id, role=ClinicMembership.Role.CLINIC_ADMIN)
    if invitation.status != ClinicInvitation.Status.PENDING:
        raise MembershipConflict('La invitación ya fue resuelta.')
    invitation.status = ClinicInvitation.Status.REVOKED
    invitation.resolved_at = timezone.now()
    invitation.save(update_fields=['status', 'resolved_at'])
    AuditEvent.objects.create(clinic=clinic, actor=actor, action='PLATFORM_INITIAL_ADMIN_INVITATION_REVOKED',
                              resource_type='clinic_invitation', resource_id=str(invitation.pk), request_id=request_id)

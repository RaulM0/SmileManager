"""Invitation domain operations; raw tokens must only be delivered privately."""
import hashlib
import secrets
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from Usuarios.models import AuditEvent, Clinic, ClinicInvitation, ClinicMembership, InvitationEmailLock
from .memberships import MembershipConflict


def _digest(token):
    return hashlib.sha256(token.encode('ascii')).hexdigest()


def can_activate_clinic(invitation):
    return (
        invitation.activates_clinic
        and invitation.role == ClinicMembership.Role.CLINIC_ADMIN
        and invitation.clinic.status == Clinic.Status.INACTIVE
        and not ClinicMembership.objects.filter(clinic_id=invitation.clinic_id).exists()
    )


def invitation_clinic_available(invitation):
    return invitation.clinic.status == Clinic.Status.ACTIVE or can_activate_clinic(invitation)


def preview_registration(token):
    try:
        if not isinstance(token, str) or len(token) != 43:
            raise ValueError
        digest = _digest(token)
    except (UnicodeEncodeError, ValueError):
        raise PermissionDenied('Invitación no válida o vencida.')
    invitation = ClinicInvitation.objects.select_related('clinic').filter(
        token_hash=digest, status=ClinicInvitation.Status.PENDING,
        expires_at__gt=timezone.now(),
    ).first()
    if invitation is None or not invitation_clinic_available(invitation):
        raise PermissionDenied('Invitación no válida o vencida.')
    return invitation


def preview_invitation(*, user, token):
    try:
        if not isinstance(token, str) or len(token) != 43:
            raise ValueError
        digest = _digest(token)
    except (UnicodeEncodeError, ValueError):
        raise PermissionDenied('Invitación no válida o vencida.')
    invitation = ClinicInvitation.objects.select_related('clinic').filter(
        token_hash=digest, status=ClinicInvitation.Status.PENDING,
        expires_at__gt=timezone.now(),
    ).first()
    account = get_user_model().objects.filter(pk=user.pk, is_active=True).first()
    if invitation is None or not invitation_clinic_available(invitation) or account is None or not account.email or account.email.strip().casefold() != invitation.email:
        raise PermissionDenied('Invitación no válida o vencida.')
    return invitation


def _admin(clinic, actor):
    return clinic.status == Clinic.Status.ACTIVE and ClinicMembership.objects.filter(
        clinic=clinic, user_id=actor.pk, user__is_active=True,
        role=ClinicMembership.Role.CLINIC_ADMIN, status=ClinicMembership.Status.ACTIVE,
    ).exists()


@transaction.atomic
def create_invitation(*, actor, clinic_id, email, role, request_id):
    clinic = get_object_or_404(Clinic.objects.select_for_update(), pk=clinic_id)
    if not _admin(clinic, actor):
        raise PermissionDenied('Operación no autorizada.')
    email = email.strip().casefold()
    try:
        validate_email(email)
    except DjangoValidationError as exc:
        raise ValidationError({'email': 'Correo no válido.'}) from exc
    if len(email) > 254 or role not in ClinicMembership.Role.values:
        raise ValidationError('Datos de invitación no válidos.')
    now = timezone.now()
    pending = ClinicInvitation.objects.filter(clinic=clinic, email=email, status=ClinicInvitation.Status.PENDING)
    pending.filter(expires_at__lte=now).update(status=ClinicInvitation.Status.REVOKED, resolved_at=now)
    if pending.exists():
        raise MembershipConflict('Ya existe una invitación pendiente para ese correo.')
    token = secrets.token_urlsafe(32)
    invitation = ClinicInvitation.objects.create(clinic=clinic, email=email, role=role, token_hash=_digest(token),
                                                 invited_by=actor, expires_at=now + timedelta(days=7))
    AuditEvent.objects.create(clinic=clinic, actor=actor, action='CLINIC_INVITATION_CREATED',
                              resource_type='clinic_invitation', resource_id=str(invitation.pk), request_id=request_id)
    return invitation, token


@transaction.atomic
def resolve_invitation(*, user, token, accept, request_id):
    # Invalid tokens and accounts get the same response.
    try:
        if not isinstance(token, str) or len(token) != 43:
            raise ValueError
        digest = _digest(token)
    except (UnicodeEncodeError, ValueError):
        raise PermissionDenied('Invitación no válida o vencida.')
    reference = ClinicInvitation.objects.filter(token_hash=digest).values('clinic_id').first()
    if reference is None:
        raise PermissionDenied('Invitación no válida o vencida.')
    clinic = Clinic.objects.select_for_update().get(pk=reference['clinic_id'])
    invitation = ClinicInvitation.objects.select_for_update().get(token_hash=digest)
    account = get_user_model().objects.select_for_update().filter(pk=user.pk, is_active=True).first()
    if (account is None or not account.email or account.email.strip().casefold() != invitation.email
            or not invitation_clinic_available(invitation) or invitation.status != ClinicInvitation.Status.PENDING
            or invitation.expires_at <= timezone.now()):
        raise PermissionDenied('Invitación no válida o vencida.')
    if accept:
        if can_activate_clinic(invitation):
            clinic.status = Clinic.Status.ACTIVE
            clinic.save(update_fields=['status', 'updated_at'])
            AuditEvent.objects.create(clinic=clinic, actor=account, action='CLINIC_ACTIVATED_ON_INVITATION',
                                      resource_type='clinic', resource_id=str(clinic.pk), request_id=request_id)
        membership = ClinicMembership.objects.select_for_update().filter(clinic=clinic, user=account).first()
        if membership and membership.status != ClinicMembership.Status.REVOKED:
            raise MembershipConflict('La membresía ya existe; contacta al administrador de la clínica.')
        if membership is None:
            membership = ClinicMembership(clinic=clinic, user=account)
        membership.role = invitation.role
        membership.status = ClinicMembership.Status.ACTIVE
        membership.joined_at = timezone.now()
        membership.invited_by = invitation.invited_by
        membership.save()
        invitation.status = ClinicInvitation.Status.ACCEPTED
    else:
        invitation.status = ClinicInvitation.Status.REJECTED
    invitation.resolved_at = timezone.now()
    invitation.save(update_fields=['status', 'resolved_at'])
    AuditEvent.objects.create(clinic=clinic, actor=account, action='CLINIC_INVITATION_ACCEPTED' if accept else 'CLINIC_INVITATION_REJECTED',
                              resource_type='clinic_invitation', resource_id=str(invitation.pk), request_id=request_id)
    return invitation


@transaction.atomic
def register_with_invitation(*, token, username, password, request_id):
    """Possession of the invitation proves access to the invited address."""
    try:
        if not isinstance(token, str) or len(token) != 43:
            raise ValueError
        digest = _digest(token)
    except (ValueError, UnicodeEncodeError):
        raise PermissionDenied('Invitación no válida o vencida.')
    reference = ClinicInvitation.objects.filter(token_hash=digest).values('clinic_id').first()
    if reference is None:
        raise PermissionDenied('Invitación no válida o vencida.')
    clinic = Clinic.objects.select_for_update().get(pk=reference['clinic_id'])
    invitation = ClinicInvitation.objects.select_for_update().get(token_hash=digest)
    if (not invitation_clinic_available(invitation) or invitation.status != ClinicInvitation.Status.PENDING
            or invitation.expires_at <= timezone.now()):
        raise PermissionDenied('Invitación no válida o vencida.')
    User = get_user_model()
    email_hash = hashlib.sha256(invitation.email.encode('utf-8')).hexdigest()
    InvitationEmailLock.objects.get_or_create(email_hash=email_hash)
    InvitationEmailLock.objects.select_for_update().get(email_hash=email_hash)
    if User.objects.filter(email__iexact=invitation.email).exists():
        raise ValidationError({'detail': 'No fue posible crear la cuenta con esos datos. Inicia sesión si ya tienes una cuenta.'})
    user = User(username=username, email=invitation.email)
    try:
        user.full_clean(exclude=['password'], validate_unique=False, validate_constraints=False)
        validate_password(password, user)
    except DjangoValidationError as exc:
        raise ValidationError({'detail': exc.messages}) from exc
    user.set_password(password)
    try:
        with transaction.atomic():
            user.save(force_insert=True)
    except IntegrityError as exc:
        raise ValidationError({'detail': 'No fue posible crear la cuenta con esos datos.'}) from exc
    resolve_invitation(user=user, token=token, accept=True, request_id=request_id)
    return user


@transaction.atomic
def revoke_invitation(*, actor, clinic_id, invitation_id, request_id):
    clinic = get_object_or_404(Clinic.objects.select_for_update(), pk=clinic_id)
    if not _admin(clinic, actor):
        raise PermissionDenied('Operación no autorizada.')
    invitation = get_object_or_404(ClinicInvitation.objects.select_for_update(), pk=invitation_id, clinic=clinic)
    if invitation.status != ClinicInvitation.Status.PENDING:
        raise MembershipConflict('La invitación ya fue resuelta.')
    invitation.status = ClinicInvitation.Status.REVOKED
    invitation.resolved_at = timezone.now()
    invitation.save(update_fields=['status', 'resolved_at'])
    AuditEvent.objects.create(clinic=clinic, actor=actor, action='CLINIC_INVITATION_REVOKED',
                              resource_type='clinic_invitation', resource_id=str(invitation.pk), request_id=request_id)

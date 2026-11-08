import uuid

from django.conf import settings
from django.db import models
from django.contrib.auth.models import User


class PlatformAdmin(models.Model):
    """Explicit product role; Django staff and superuser flags are separate."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='platform_admin')
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        permissions = [('manage_platform_roles', 'Can manage platform administrator roles')]


class Clinic(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        SUSPENDED = 'SUSPENDED', 'Suspended'
        INACTIVE = 'INACTIVE', 'Inactive'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=150, unique=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.INACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.CheckConstraint(condition=models.Q(status__in=['ACTIVE', 'SUSPENDED', 'INACTIVE']), name='clinic_valid_status')]

    def __str__(self):
        return self.name


class ClinicMembership(models.Model):
    class Role(models.TextChoices):
        CLINIC_ADMIN = 'CLINIC_ADMIN', 'Clinic administrator'
        DOCTOR = 'DOCTOR', 'Doctor'
        STAFF = 'STAFF', 'Staff'

    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        SUSPENDED = 'SUSPENDED', 'Suspended'
        REVOKED = 'REVOKED', 'Revoked'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    clinic = models.ForeignKey(Clinic, on_delete=models.PROTECT, related_name='memberships')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='clinic_memberships')
    role = models.CharField(max_length=12, choices=Role.choices)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.SUSPENDED)
    invited_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='invited_clinic_memberships')
    joined_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['clinic', 'user'], name='unique_clinic_membership'),
            models.CheckConstraint(condition=models.Q(role__in=['CLINIC_ADMIN', 'DOCTOR', 'STAFF']), name='membership_valid_role'),
            models.CheckConstraint(condition=models.Q(status__in=['ACTIVE', 'SUSPENDED', 'REVOKED']), name='membership_valid_status'),
        ]


class ClinicInvitation(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        ACCEPTED = 'ACCEPTED', 'Accepted'
        REJECTED = 'REJECTED', 'Rejected'
        REVOKED = 'REVOKED', 'Revoked'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    clinic = models.ForeignKey(Clinic, on_delete=models.PROTECT, related_name='invitations')
    email = models.EmailField(max_length=254)
    role = models.CharField(max_length=12, choices=ClinicMembership.Role.choices)
    token_hash = models.CharField(max_length=64, unique=True)
    status = models.CharField(max_length=8, choices=Status.choices, default=Status.PENDING)
    invited_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name='clinic_invitations_sent')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(role__in=['CLINIC_ADMIN', 'DOCTOR', 'STAFF']), name='invitation_valid_role'),
            models.CheckConstraint(condition=models.Q(status__in=['PENDING', 'ACCEPTED', 'REJECTED', 'REVOKED']), name='invitation_valid_status'),
            models.UniqueConstraint(fields=['clinic', 'email'], condition=models.Q(status='PENDING'), name='unique_pending_clinic_invitation'),
        ]


class InvitationEmailLock(models.Model):
    """Serialize account creation for the same normalized invitation address."""
    email_hash = models.CharField(primary_key=True, max_length=64)

class Perfil(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    clinica_nombre = models.CharField('Nombre de la Clínica', max_length=100, blank=True, null=True)
    telefono = models.CharField('Teléfono', max_length=20, blank=True, null=True)
    direccion = models.CharField('Dirección', max_length=255, blank=True, null=True)
    extra = models.TextField('Notas', blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - Perfil"


class AuditEvent(models.Model):
    clinic = models.ForeignKey(Clinic, null=True, blank=True, on_delete=models.PROTECT, related_name='audit_events')
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    actor = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='audit_events')
    action = models.CharField(max_length=64, db_index=True)
    resource_type = models.CharField(max_length=40, blank=True)
    resource_id = models.CharField(max_length=64, blank=True)
    request_id = models.UUIDField(db_index=True)
    outcome = models.CharField(max_length=16, default='success')

    class Meta:
        ordering = ['-timestamp', '-id']
        permissions = [('access_system_backoffice', 'Can access system backoffice')]

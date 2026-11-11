"""Versioned documents and independent consent evidence; legacy stays read-only."""
import uuid
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class ImmutableQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise ValidationError('El documento es inmutable. Registra una nueva versión o adenda.')

    def delete(self):
        raise ValidationError('El documento forma parte del expediente y no admite borrado ordinario.')


class ImmutableDocument(models.Model):
    objects = ImmutableQuerySet.as_manager()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if self.pk and type(self).objects.filter(pk=self.pk).exists():
            raise ValidationError('El documento es inmutable. Registra una nueva versión o adenda.')
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError('El documento no admite borrado ordinario.')


class PrivacyNotice(ImmutableDocument):
    clinic = models.ForeignKey('Usuarios.Clinic', on_delete=models.PROTECT)
    version = models.PositiveIntegerField()
    body = models.JSONField()
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    approved_name = models.CharField(max_length=300)
    published_at = models.DateTimeField(default=timezone.now)
    content_sha256 = models.CharField(max_length=64)
    integrity_seal = models.CharField(max_length=64)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['clinic', 'version'], name='unique_privacy_notice_version')]


class ConsentTemplate(ImmutableDocument):
    clinic = models.ForeignKey('Usuarios.Clinic', on_delete=models.PROTECT)
    kind = models.CharField(max_length=12, choices=[('CLINICAL', 'Clínico'), ('PRIVACY', 'Datos personales')])
    version = models.PositiveIntegerField()
    title = models.CharField(max_length=250)
    text = models.TextField()
    privacy_notice = models.ForeignKey(PrivacyNotice, null=True, blank=True, on_delete=models.PROTECT)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    approved_name = models.CharField(max_length=300)
    published_at = models.DateTimeField(default=timezone.now)
    content_sha256 = models.CharField(max_length=64)
    integrity_seal = models.CharField(max_length=64)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['clinic', 'kind', 'version'], name='unique_consent_template_version')]


def evidence_key(instance, filename):
    extension = '.pdf' if filename.lower().endswith('.pdf') else '.image'
    return f'tenants/{instance.clinic_id}/patients/{instance.patient_id}/consents/evidence/{uuid.uuid4().hex}{extension}'


class ConsentEvidence(ImmutableDocument):
    clinic = models.ForeignKey('Usuarios.Clinic', on_delete=models.PROTECT)
    patient = models.ForeignKey('Pacientes.Paciente', on_delete=models.PROTECT)
    template = models.ForeignKey(ConsentTemplate, on_delete=models.PROTECT)
    template_sha256 = models.CharField(max_length=64)
    supersedes = models.OneToOneField('self', null=True, blank=True, on_delete=models.PROTECT, related_name='replacement')
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    recorded_name = models.CharField(max_length=300)
    recorded_at = models.DateTimeField()
    signer_name = models.CharField(max_length=300)
    signer_role = models.CharField(max_length=14, choices=[('PATIENT', 'Paciente'), ('REPRESENTATIVE', 'Representante')])
    representative_basis = models.TextField(blank=True)
    signed_on = models.DateField()
    signed_document = models.FileField(upload_to=evidence_key)
    file_sha256 = models.CharField(max_length=64)
    content_sha256 = models.CharField(max_length=64)
    integrity_seal = models.CharField(max_length=64)


class ConsentRevocation(ImmutableDocument):
    evidence = models.OneToOneField(ConsentEvidence, on_delete=models.PROTECT, related_name='revocation')
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    recorded_name = models.CharField(max_length=300)
    reason = models.TextField()
    created_at = models.DateTimeField()
    content_sha256 = models.CharField(max_length=64)
    integrity_seal = models.CharField(max_length=64)


class ConsultationAddendum(ImmutableDocument):
    consultation = models.ForeignKey('Pacientes.Consulta', on_delete=models.PROTECT, related_name='addenda')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    author_name = models.CharField(max_length=300)
    text = models.TextField()
    base_content_sha256 = models.CharField(max_length=64)
    created_at = models.DateTimeField()
    content_sha256 = models.CharField(max_length=64)
    integrity_seal = models.CharField(max_length=64)

    class Meta:
        ordering = ['created_at', 'id']

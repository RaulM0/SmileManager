import os
import uuid

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError

class Paciente(models.Model):
    # Nullable during expand/backfill. Existing ownership cannot safely be inferred.
    clinic = models.ForeignKey('Usuarios.Clinic', null=True, blank=True, on_delete=models.PROTECT, related_name='patients')
    nombre = models.CharField(max_length=50)
    appat = models.CharField(max_length=50)
    apmat = models.CharField(max_length=50)
    fecha_nacimiento = models.DateField()
    genero = models.CharField(max_length=1, choices=[('M', 'Masculino'), ('F', 'Femenino')])
    telefono = models.CharField(max_length=10)
    email = models.EmailField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    estatus = models.CharField(max_length=1, choices=[('A', 'Activo'), ('I', 'Inactivo')], default='A')
    medico = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="pacientes")

    class Meta:
        verbose_name = 'Paciente'
        verbose_name_plural = 'Pacientes'
        constraints = [
            models.UniqueConstraint(fields=['telefono', 'medico'], condition=models.Q(clinic__isnull=True), name='legacy_phone_doctor_uniq'),
            models.UniqueConstraint(fields=['email', 'medico'], condition=models.Q(clinic__isnull=True), name='legacy_email_doctor_uniq'),
            models.UniqueConstraint(fields=['clinic', 'telefono', 'medico'], condition=models.Q(clinic__isnull=False), name='clinic_phone_doctor_uniq'),
            models.UniqueConstraint(fields=['clinic', 'email', 'medico'], condition=models.Q(clinic__isnull=False), name='clinic_email_doctor_uniq'),
        ]

    def __str__(self):
        return f"{self.nombre} {self.appat}"


class AntescedentesMedicos(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='antecedentes_medicos')
    medico = models.ForeignKey(User, on_delete=models.CASCADE)

    # Detalles médicos
    tratamiento_medico = models.BooleanField(null=True, blank=True, default=None, verbose_name="¿Está en tratamiento médico?")
    problemas_cardiacos = models.BooleanField(null=True, blank=True, default=None, verbose_name="¿Tiene problemas cardíacos?")
    problemas_coagulacion = models.BooleanField(null=True, blank=True, default=None, verbose_name="¿Tiene problemas de coagulación?")
    epilepsia = models.BooleanField(null=True, blank=True, default=None, verbose_name="Epilepsia/Convulsiones")
    gastritis = models.BooleanField(null=True, blank=True, default=None, verbose_name="Gastritis/Úlceras")
    hipertension = models.BooleanField(null=True, blank=True, default=None, verbose_name="Hipertensión")
    anemia = models.BooleanField(null=True, blank=True, default=None, verbose_name="Anemia")
    embarazo = models.BooleanField(null=True, blank=True, default=None, verbose_name="Embarazo/Sospecha de embarazo")
    alergia_medicamentos = models.BooleanField(null=True, blank=True, default=None, verbose_name="Alergia a algún medicamento")
    alergia_especifica = models.BooleanField(null=True, blank=True, default=None, verbose_name="Alergia específica")
    discapacidad = models.BooleanField(null=True, blank=True, default=None, verbose_name="Discapacidad")
    fuma = models.BooleanField(null=True, blank=True, default=None, verbose_name="¿Fuma?")

    # Detalles dentales
    respiracion_bucal = models.BooleanField(null=True, blank=True, default=None, verbose_name="Respiración bucal")
    morder_unas = models.BooleanField(null=True, blank=True, default=None, verbose_name="Morderse las uñas")
    chupar_dedo = models.BooleanField(null=True, blank=True, default=None, verbose_name="Chupar dedo o labios")
    rechinar_dientes = models.BooleanField(null=True, blank=True, default=None, verbose_name="Rechinar los dientes")
    sobremordida_vertical = models.BooleanField(null=True, blank=True, default=None, verbose_name="Sobremordida vertical")
    sobremordida_horizontal = models.BooleanField(null=True, blank=True, default=None, verbose_name="Sobremordida horizontal")
    mordida_cruzada = models.BooleanField(null=True, blank=True, default=None, verbose_name="Mordida cruzada")
    mordida_abierta = models.BooleanField(null=True, blank=True, default=None, verbose_name="Mordida abierta")
    desgaste = models.BooleanField(null=True, blank=True, default=None, verbose_name="Desgaste - Abrasion")
    problemas_atm = models.BooleanField(null=True, blank=True, default=None, verbose_name="Problemas ATM chasquidos")
    consumo_citricos = models.BooleanField(null=True, blank=True, default=None, verbose_name="Consumo frecuente de cítricos")
    sangrado_encias = models.BooleanField(null=True, blank=True, default=None, verbose_name="Sangrado de encías")

    # Adicionales
    alergias = models.TextField(blank=True, null=True)
    medicamentos = models.TextField(blank=True, null=True)
    cirugias_previas = models.TextField(blank=True, null=True)
    otros = models.TextField(blank=True, null=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    version = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Antecedente Medico'
        verbose_name_plural = 'Antecedentes Medicos'
        ordering = ['-created']

    def __str__(self):
        return f"Antecedentes de {self.paciente.nombre} {self.paciente.appat}"


class Consulta(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='consultas')
    medico = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha_consulta = models.DateTimeField()
    motivo_consulta = models.TextField()
    diagnostico = models.TextField(blank=True, null=True)
    tratamiento = models.TextField(blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=8, choices=[('DRAFT', 'Borrador'), ('CLOSED', 'Cerrado'), ('LEGACY', 'Histórico')], default='DRAFT')
    author_name = models.CharField(max_length=300, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    content_sha256 = models.CharField(max_length=64, blank=True)
    integrity_seal = models.CharField(max_length=64, blank=True)

    def save(self, *args, **kwargs):
        if self.pk and type(self).objects.filter(pk=self.pk, status='CLOSED').exists():
            raise ValidationError('El documento está cerrado; registra una adenda.')
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.status == 'CLOSED':
            raise ValidationError('El documento cerrado no admite borrado ordinario.')
        return super().delete(*args, **kwargs)

    class Meta:
        verbose_name = 'Consulta'
        verbose_name_plural = 'Consultas'

    def __str__(self):
        return f"Consulta de {self.paciente.nombre} {self.paciente.appat} el {self.fecha_consulta.strftime('%Y-%m-%d')}"


def clinical_image_storage_key(instance, filename):
    """New tenant files use non-identifying names; legacy paths stay compatible."""
    if instance.paciente.clinic_id is None:
        return os.path.join('imagenes_clinicas', os.path.basename(filename))
    extension = os.path.splitext(filename)[1].lower()
    if extension not in {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tif', '.tiff'}:
        extension = '.bin'
    return f'tenants/{instance.paciente.clinic_id}/patients/{instance.paciente_id}/images/{uuid.uuid4().hex}{extension}'


def clinical_result_storage_key(instance, filename):
    if instance.paciente.clinic_id is None:
        return os.path.join('resultados', os.path.basename(filename))
    extension = os.path.splitext(filename)[1].lower()
    if extension not in {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tif', '.tiff'}:
        extension = '.bin'
    return f'tenants/{instance.paciente.clinic_id}/patients/{instance.paciente_id}/ai-results/{uuid.uuid4().hex}{extension}'


class ImagenesClinicas(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='imagenes_clinicas')
    consulta = models.ForeignKey(Consulta, on_delete=models.CASCADE, related_name='imagenes_clinicas', null=True, blank=True)
    tipo_imagen = models.CharField(max_length=50)
    descripcion = models.TextField(blank=True, null=True)
    imagen = models.ImageField(upload_to=clinical_image_storage_key)
    resultados = models.ImageField(upload_to=clinical_result_storage_key, null=True, blank=True)
    fecha_subida = models.DateTimeField(auto_now_add=True)
    medico = models.ForeignKey(User, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Imagen Clinica'
        verbose_name_plural = 'Imagenes Clinicas'

    def __str__(self):
        if self.consulta:
            fecha = self.consulta.fecha_consulta.strftime('%Y-%m-%d')
            return f"Imagen clínica de {self.paciente.nombre} {self.paciente.appat} ({fecha})"
        return f"Imagen clínica de {self.paciente.nombre} {self.paciente.appat}"


class Odontograma(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='odontogramas')
    medico = models.ForeignKey(User, on_delete=models.CASCADE)
    dientes_permanentes = models.JSONField(default=dict)
    dientes_deciduos = models.JSONField(default=dict)
    resumen_clinico = models.JSONField(default=dict)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    version = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Odontograma de {self.paciente.nombre} {self.paciente.appat}"


class ClinicalRevision(models.Model):
    """Snapshot clínico separado del log de auditoría, sin archivos."""
    # Revisions can survive without a patient, so retain independent provenance.
    clinic = models.ForeignKey('Usuarios.Clinic', null=True, blank=True, on_delete=models.PROTECT, related_name='clinical_revisions')
    patient = models.ForeignKey(Paciente, null=True, on_delete=models.SET_NULL, related_name='clinical_revisions')
    actor = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    resource_type = models.CharField(max_length=32)
    resource_id = models.BigIntegerField()
    version = models.PositiveIntegerField()
    snapshot = models.JSONField()
    created = models.DateTimeField(default=timezone.now)
    actor_name = models.CharField(max_length=300, blank=True)
    content_sha256 = models.CharField(max_length=64, blank=True)
    integrity_seal = models.CharField(max_length=64, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['resource_type', 'resource_id', 'version'], name='unique_clinical_revision')]


def study_before_storage_key(instance, filename):
    if instance.paciente.clinic_id is None:
        return os.path.join('estudios', 'antes', os.path.basename(filename))
    extension = os.path.splitext(filename)[1].lower()
    if extension not in {'.jpg', '.jpeg', '.png', '.gif', '.webp'}:
        extension = '.bin'
    return f'tenants/{instance.paciente.clinic_id}/patients/{instance.paciente_id}/studies/before/{uuid.uuid4().hex}{extension}'


def study_after_storage_key(instance, filename):
    if instance.paciente.clinic_id is None:
        return os.path.join('estudios', 'despues', os.path.basename(filename))
    extension = os.path.splitext(filename)[1].lower()
    if extension not in {'.jpg', '.jpeg', '.png', '.gif', '.webp'}:
        extension = '.bin'
    return f'tenants/{instance.paciente.clinic_id}/patients/{instance.paciente_id}/studies/after/{uuid.uuid4().hex}{extension}'


class EstudioComparativo(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='estudios_comparativos')
    fecha_inicio = models.DateField()
    diagnostico = models.CharField(max_length=255, blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)
    medico = models.ForeignKey(User, on_delete=models.CASCADE)

    # Imágenes ANTES
    antes_oclusal_superior = models.ImageField(upload_to=study_before_storage_key, null=True, blank=True)
    antes_lateral_izquierda = models.ImageField(upload_to=study_before_storage_key, null=True, blank=True)
    antes_frontal = models.ImageField(upload_to=study_before_storage_key, null=True, blank=True)
    antes_lateral_derecha = models.ImageField(upload_to=study_before_storage_key, null=True, blank=True)
    antes_oclusal_inferior = models.ImageField(upload_to=study_before_storage_key, null=True, blank=True)

    # Imágenes DESPUÉS
    despues_perfil = models.ImageField(upload_to=study_after_storage_key, null=True, blank=True)
    despues_semiperfil = models.ImageField(upload_to=study_after_storage_key, null=True, blank=True)
    despues_retrato_frontal = models.ImageField(upload_to=study_after_storage_key, null=True, blank=True)
    despues_retrato_sonrisa = models.ImageField(upload_to=study_after_storage_key, null=True, blank=True)

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Estudio Comparativo"
        verbose_name_plural = "Estudios Comparativos"

    def __str__(self):
        return f"Estudio - {self.paciente.nombre} {self.paciente.appat}"


def consent_identity_storage_key(instance, filename):
    if instance.paciente.clinic_id is None:
        return os.path.join('consentimientos', 'ine', os.path.basename(filename))
    extension = os.path.splitext(filename)[1].lower()
    if extension not in {'.pdf', '.jpg', '.jpeg', '.png', '.gif', '.webp'}:
        extension = '.bin'
    return f'tenants/{instance.paciente.clinic_id}/patients/{instance.paciente_id}/consents/identity/{uuid.uuid4().hex}{extension}'


def consent_pdf_storage_key(instance, filename):
    if instance.paciente.clinic_id is None:
        return os.path.join('consentimientos', 'pdf', os.path.basename(filename))
    return f'tenants/{instance.paciente.clinic_id}/patients/{instance.paciente_id}/consents/documents/{uuid.uuid4().hex}.pdf'


class Consentimiento(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE)
    medico = models.ForeignKey(User, on_delete=models.CASCADE)
    texto = models.TextField()
    fecha_aceptacion = models.DateTimeField(null=True, blank=True)
    archivo_ine = models.FileField(upload_to=consent_identity_storage_key, null=True, blank=True)
    pdf_generado = models.FileField(upload_to=consent_pdf_storage_key, null=True, blank=True)

    def __str__(self):
        if self.fecha_aceptacion:
            fecha = self.fecha_aceptacion.strftime('%d/%m/%Y')
        else:
            fecha = "Sin fecha"
        return f"Consentimiento de {self.paciente.nombre} - {fecha}"


from .documents import PrivacyNotice, ConsentTemplate, ConsentEvidence, ConsentRevocation, ConsultationAddendum  # noqa: E402,F401


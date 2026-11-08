from datetime import datetime
from django.conf import settings
from django.db import transaction

from rest_framework.exceptions import PermissionDenied, ValidationError

from Pacientes.models import Paciente
from .clinical_access import lock_authorized_patient


UPPERCASE_FIELDS = ('nombre', 'appat', 'apmat', 'email')


def normalize_patient_data(data):
    normalized = dict(data)
    for field in UPPERCASE_FIELDS:
        value = normalized.get(field)
        if isinstance(value, str):
            normalized[field] = value.upper()
    return normalized


def validate_patient_uniqueness(*, medico, telefono, email, clinic_id=None, instance=None):
    patients = Paciente.objects.filter(medico=medico, clinic_id=clinic_id)
    if instance is not None:
        patients = patients.exclude(pk=instance.pk)
    errors = {}
    if patients.filter(telefono=telefono).exists():
        errors['telefono'] = ['El teléfono ya está registrado para tu consultorio.']
    if patients.filter(email=email).exists():
        errors['email'] = ['El email ya está registrado para tu consultorio.']
    if errors:
        raise ValidationError(errors)


@transaction.atomic
def create_patient(*, medico, validated_data):
    data = normalize_patient_data(validated_data)
    if set(data) & {'clinic', 'medico', 'medico_id'}:
        raise PermissionDenied('La clínica y el médico se asignan desde el contexto autorizado.')
    clinic_id = data.get('clinic_id')
    if clinic_id is None:
        if not settings.LEGACY_CLINICAL_API_ENABLED:
            raise PermissionDenied('La creación de pacientes requiere una clínica autorizada.')
        from Usuarios.models import ClinicMembership
        if ClinicMembership.objects.filter(user_id=medico.pk).exists():
            raise PermissionDenied('Selecciona una clínica en una ruta compatible para crear pacientes.')
    else:
        from api.tenant_context import lock_clinic_capability
        lock_clinic_capability(medico, clinic_id, 'clinical.assigned')
    validate_patient_uniqueness(
        medico=medico, telefono=data['telefono'], email=data['email'], clinic_id=clinic_id,
    )
    return Paciente.objects.create(medico=medico, **data)


@transaction.atomic
def update_patient(*, patient, medico, validated_data, clinic_id=None):
    patient = lock_authorized_patient(user=medico, patient_id=patient.pk, clinic_id=clinic_id)
    data = normalize_patient_data(validated_data)
    if set(data) & {'clinic', 'clinic_id', 'medico', 'medico_id'}:
        raise PermissionDenied('La clínica y el médico se asignan desde el contexto autorizado.')
    telefono = data.get('telefono', patient.telefono)
    email = data.get('email', patient.email)
    validate_patient_uniqueness(
        medico=medico, telefono=telefono, email=email, clinic_id=patient.clinic_id, instance=patient,
    )
    for field, value in data.items():
        setattr(patient, field, value)
    patient.save()
    return patient


@transaction.atomic
def deactivate_patient(*, patient, user, clinic_id=None):
    patient = lock_authorized_patient(user=user, patient_id=patient.pk, clinic_id=clinic_id)
    patient.estatus = 'I'
    patient.save(update_fields=['estatus', 'updated'])
    return patient


def legacy_age(patient):
    return (datetime.today().date() - patient.fecha_nacimiento).days // 365

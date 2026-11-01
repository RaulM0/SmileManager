from datetime import datetime

from rest_framework.exceptions import ValidationError

from Pacientes.models import Paciente


UPPERCASE_FIELDS = ('nombre', 'appat', 'apmat', 'email')


def normalize_patient_data(data):
    normalized = dict(data)
    for field in UPPERCASE_FIELDS:
        value = normalized.get(field)
        if isinstance(value, str):
            normalized[field] = value.upper()
    return normalized


def validate_patient_uniqueness(*, medico, telefono, email, instance=None):
    patients = Paciente.objects.filter(medico=medico)
    if instance is not None:
        patients = patients.exclude(pk=instance.pk)
    errors = {}
    if patients.filter(telefono=telefono).exists():
        errors['telefono'] = ['El teléfono ya está registrado para tu consultorio.']
    if patients.filter(email=email).exists():
        errors['email'] = ['El email ya está registrado para tu consultorio.']
    if errors:
        raise ValidationError(errors)


def create_patient(*, medico, validated_data):
    data = normalize_patient_data(validated_data)
    validate_patient_uniqueness(
        medico=medico, telefono=data['telefono'], email=data['email'],
    )
    return Paciente.objects.create(medico=medico, **data)


def update_patient(*, patient, medico, validated_data):
    data = normalize_patient_data(validated_data)
    telefono = data.get('telefono', patient.telefono)
    email = data.get('email', patient.email)
    validate_patient_uniqueness(
        medico=medico, telefono=telefono, email=email, instance=patient,
    )
    for field, value in data.items():
        setattr(patient, field, value)
    patient.save()
    return patient


def deactivate_patient(patient):
    patient.estatus = 'I'
    patient.save(update_fields=['estatus', 'updated'])
    return patient


def legacy_age(patient):
    return (datetime.today().date() - patient.fecha_nacimiento).days // 365

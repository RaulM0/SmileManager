from datetime import time

from django.utils import timezone
from django.db import transaction
from rest_framework.exceptions import ValidationError
from rest_framework.exceptions import APIException
from django.shortcuts import get_object_or_404
from Pacientes.access import clinic_clinical_queryset, scoped


class InvalidStateTransition(APIException):
    status_code = 409
    default_detail = 'La transición de estado de la cita no está permitida.'
    default_code = 'invalid_state_transition'


def can_transition(current, target):
    return current in ('P', 'C', 'A') and (target == current or (current == 'P' and target in ('C', 'A')))


def validate_appointment_schedule(fecha, hora):
    errors = {}
    if fecha < timezone.localdate():
        errors['fecha'] = ['No puedes registrar una cita en una fecha pasada.']
    if hora < time(8, 0) or hora > time(20, 0):
        errors['hora'] = ['La hora debe estar entre las 08:00 y las 20:00.']
    if errors:
        raise ValidationError(errors)


@transaction.atomic
def save_appointment(*, user, appointment=None, patient, validated_data, clinic_id=None):
    from Citas.models import Cita
    from Pacientes.models import Paciente

    if appointment is not None:
        rows = clinic_clinical_queryset(user, clinic_id, Cita) if clinic_id is not None else scoped(user, Cita)
        appointment = get_object_or_404(rows.select_for_update(of=('self',)), pk=appointment.pk)
    if patient is not None or (clinic_id is not None and appointment is not None):
        patient_id = patient.pk if patient is not None else appointment.paciente_id
        rows = clinic_clinical_queryset(user, clinic_id, Paciente) if clinic_id is not None else scoped(user, Paciente)
        patient = get_object_or_404(rows.select_for_update(of=('self',)), pk=patient_id)

    fecha = validated_data.get('fecha', appointment.fecha if appointment else None)
    hora = validated_data.get('hora', appointment.hora if appointment else None)
    validate_appointment_schedule(fecha, hora)
    values = {
        'paciente': patient if patient is not None else appointment.paciente,
        'fecha': fecha,
        'hora': hora,
        'motivo': validated_data.get('motivo', appointment.motivo if appointment else 'Ninguno'),
        'estatus': validated_data.get('estatus', appointment.estatus if appointment else 'P'),
        'observaciones': validated_data.get('observaciones', appointment.observaciones if appointment else 'Ninguna'),
    }
    if appointment and not can_transition(appointment.estatus, values['estatus']):
        raise InvalidStateTransition()
    if values['estatus'] not in ('P', 'C', 'A'):
        raise ValidationError({'estatus': ['Estado no válido.']})
    if appointment is None:
        return Cita.objects.create(**values)
    for field, value in values.items():
        setattr(appointment, field, value)
    appointment.save()
    return appointment


@transaction.atomic
def transition_appointment(*, user, appointment, target, clinic_id=None):
    from Citas.models import Cita
    rows = clinic_clinical_queryset(user, clinic_id, Cita) if clinic_id is not None else scoped(user, Cita)
    appointment = get_object_or_404(rows.select_for_update(of=('self',)), pk=appointment.pk)
    if clinic_id is not None:
        from Pacientes.models import Paciente
        patients = clinic_clinical_queryset(user, clinic_id, Paciente).select_for_update(of=('self',))
        get_object_or_404(patients, pk=appointment.paciente_id)
    if not can_transition(appointment.estatus, target):
        raise InvalidStateTransition()
    if appointment.estatus != target:
        appointment.estatus = target
        appointment.save(update_fields=['estatus', 'updated'])
    return appointment

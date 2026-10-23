from datetime import time

from django.utils import timezone
from rest_framework.exceptions import ValidationError


def validate_appointment_schedule(fecha, hora):
    errors = {}
    if fecha < timezone.localdate():
        errors['fecha'] = ['No puedes registrar una cita en una fecha pasada.']
    if hora < time(8, 0) or hora > time(20, 0):
        errors['hora'] = ['La hora debe estar entre las 08:00 y las 20:00.']
    if errors:
        raise ValidationError(errors)


def save_appointment(*, appointment=None, patient, validated_data):
    from Citas.models import Cita

    fecha = validated_data.get('fecha', appointment.fecha if appointment else None)
    hora = validated_data.get('hora', appointment.hora if appointment else None)
    validate_appointment_schedule(fecha, hora)
    values = {
        'paciente': patient,
        'fecha': fecha,
        'hora': hora,
        'motivo': validated_data.get('motivo', 'Ninguno'),
        'estatus': validated_data.get('estatus', 'P'),
        'observaciones': validated_data.get('observaciones', 'Ninguna'),
    }
    if appointment is None:
        return Cita.objects.create(**values)
    for field, value in values.items():
        setattr(appointment, field, value)
    appointment.save()
    return appointment

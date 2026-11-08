"""Appointment reminders require an explicit, currently active clinic."""
from datetime import timedelta
from uuid import UUID

from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Exists, OuterRef
from django.template.loader import render_to_string
from django.utils import timezone

from Usuarios.models import Clinic, ClinicMembership
from .models import Cita


def send_appointment_reminders(*, clinic_id, now=None, dry_run=True, write=lambda message: None):
    try:
        clinic_id = UUID(str(clinic_id))
    except (ValueError, TypeError, AttributeError) as exc:
        raise ValueError('Una clínica válida es obligatoria.') from exc
    if not Clinic.objects.filter(pk=clinic_id, status=Clinic.Status.ACTIVE).exists():
        raise ValueError('La clínica no existe o no está activa.')
    now = timezone.localtime(now or timezone.now())
    end = now + timedelta(hours=24)
    doctor_membership = ClinicMembership.objects.filter(
        clinic_id=clinic_id, user_id=OuterRef('paciente__medico_id'), user__is_active=True,
        status=ClinicMembership.Status.ACTIVE, role=ClinicMembership.Role.DOCTOR,
    )
    appointments = Cita.objects.filter(
        paciente__clinic_id=clinic_id, paciente__clinic__status=Clinic.Status.ACTIVE,
        fecha__range=(now.date(), end.date()), estatus='P',
    ).annotate(doctor_authorized=Exists(doctor_membership)).filter(doctor_authorized=True)
    found = appointments.count()
    sent = errors = 0
    if dry_run:
        return {'found': found, 'sent': 0, 'errors': 0}
    for appointment in appointments.select_related('paciente', 'paciente__clinic').iterator(chunk_size=100):
        # Recheck status and membership immediately before each external action.
        if not appointments.filter(pk=appointment.pk).exists():
            continue
        if not appointment.paciente.email:
            write(f'appointment={appointment.pk} result=missing_email')
            continue
        context = {'asunto': 'Recordatorio de Cita - Clínica Dental',
                   'mensaje': f'Hola {appointment.paciente.nombre},\n\nTe recordamos tu cita el {appointment.fecha:%d/%m/%Y} a las {appointment.hora:%H:%M}.',
                   'clinic_name': appointment.paciente.clinic.name}
        try:
            html = render_to_string('emails/appointment_reminder_tenant.html', context)
            delivered = send_mail(subject='Recordatorio de cita', message=context['mensaje'],
                                  from_email=settings.DEFAULT_FROM_EMAIL, recipient_list=[appointment.paciente.email],
                                  html_message=html, fail_silently=False)
            if delivered != 1:
                raise RuntimeError('Delivery failed')
            sent += 1
            write(f'appointment={appointment.pk} result=sent')
        except Exception:
            errors += 1
            write(f'appointment={appointment.pk} result=error')
    return {'found': found, 'sent': sent, 'errors': errors}

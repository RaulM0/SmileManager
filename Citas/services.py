from datetime import timedelta
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from .models import Cita

def send_appointment_reminders(*, now=None, write=lambda message: None):
    now=now or timezone.now(); end=now+timedelta(hours=24)
    appointments=Cita.objects.filter(fecha__range=(now,end),estatus='P')
    sent=errors=0
    for appointment in appointments:
        if not appointment.paciente.email:
            write(f'Paciente {appointment.paciente.nombre} sin email'); continue
        context={'asunto':'Recordatorio de Cita - Clínica Dental','mensaje':f'''\nHola {appointment.paciente.nombre},\n\nTe recordamos que tienes una cita programada para mañana:\n\nFecha: {appointment.fecha.strftime("%d de %B de %Y")}\nHora: {appointment.hora.strftime("%I:%M %p")}\nMotivo: {appointment.motivo}\n\nPor favor, llega 10 minutos antes de tu cita.\nSi no puedes asistir, contáctanos para reagendar.\n                ''','paciente':appointment.paciente,'cita':appointment,'user':appointment.paciente.medico,'now':now}
        try:
            html=render_to_string('emails/mensaje_paciente.html',context)
            send_mail(subject='Recordatorio de Cita - Clínica Dental 🦷',message=context['mensaje'],from_email=settings.EMAIL_HOST_USER,recipient_list=[appointment.paciente.email],html_message=html,fail_silently=False)
            sent+=1; write(f'Recordatorio enviado a {appointment.paciente.nombre} ({appointment.paciente.email})')
        except Exception as exc:
            errors+=1; write(f'Error al enviar a {appointment.paciente.nombre}: {exc}')
    return {'found':appointments.count(),'sent':sent,'errors':errors}

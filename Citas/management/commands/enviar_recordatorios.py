from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from Citas.models import Cita


class Command(BaseCommand):
    help = 'Enviar recordatorios de citas 24 horas antes'

    def handle(self, *args, **kwargs):
        ahora = timezone.now()
        fin = ahora + timedelta(hours=24)

        citas_proximas = Cita.objects.filter(
            fecha__range=(ahora, fin),
            estatus='P'
        )


        enviados = 0
        errores = 0

        for cita in citas_proximas:
            if not cita.paciente.email:
                self.stdout.write(f'Paciente {cita.paciente.nombre} sin email')
                continue

            contexto = {
                'asunto': 'Recordatorio de Cita - Clínica Dental',
                'mensaje': f'''
Hola {cita.paciente.nombre},

Te recordamos que tienes una cita programada para mañana:

Fecha: {cita.fecha.strftime("%d de %B de %Y")}
Hora: {cita.hora.strftime("%I:%M %p")}
Motivo: {cita.motivo}

Por favor, llega 10 minutos antes de tu cita.
Si no puedes asistir, contáctanos para reagendar.
                ''',
                'now': timezone.now()
            }

            try:
                html_message = render_to_string('emails/mensaje_paciente.html', contexto)

                send_mail(
                    subject='Recordatorio de Cita - Clínica Dental 🦷',
                    message=contexto['mensaje'],
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[cita.paciente.email],
                    html_message=html_message,
                    fail_silently=False
                )

                enviados += 1
                self.stdout.write(f'Recordatorio enviado a {cita.paciente.nombre} ({cita.paciente.email})')

            except Exception as e:
                errores += 1
                self.stdout.write(f'Error al enviar a {cita.paciente.nombre}: {e}')

        self.stdout.write(f'\nCitas encontradas: {citas_proximas.count()}')
        self.stdout.write(f'Correos enviados: {enviados}')
        if errores > 0:
            self.stdout.write(f'Errores: {errores}')

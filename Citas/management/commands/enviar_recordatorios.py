from django.core.management.base import BaseCommand
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from datetime import timedelta
from Citas.models import Cita


class Command(BaseCommand):
    help = 'Envía recordatorios por correo 24h antes de las citas programadas'

    def handle(self, *args, **kwargs):
        hoy = timezone.localdate()
        mañana = hoy + timedelta(days=1)

        citas = Cita.objects.filter(fecha=mañana, estatus='P')
        total = 0

        for cita in citas:
            paciente = cita.paciente

            # --- Contenido del correo ---
            asunto = "🦷 Recordatorio de tu cita dental"
            contexto = {
                'paciente': paciente,
                'cita': cita,
            }

            # versión texto plano (por compatibilidad)
            texto = (
                f"Hola {paciente.nombre},\n\n"
                f"Te recordamos que mañana tienes una cita dental el "
                f"{cita.fecha.strftime('%d/%m/%Y')} a las {cita.hora.strftime('%H:%M')}.\n\n"
                f"Motivo: {cita.motivo}\n\n"
                f"Por favor llega 10 minutos antes de tu cita.\n\n"
                f"Atentamente,\nClínica Dental Sonrisa Perfecta 🦷"
            )

            # versión HTML
            html = render_to_string('emails/recordatorio_cita.html', contexto)

            # --- Envío del correo ---
            correo = EmailMultiAlternatives(
                asunto,
                texto,
                'raumillandesa@gmail.com',  # remitente
                [paciente.email]              # destinatario
            )
            correo.attach_alternative(html, 'text/html')
            correo.send()

            total += 1

        self.stdout.write(self.style.SUCCESS(f'{total} correos enviados'))

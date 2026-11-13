"""Send a synthetic message only to an explicitly selected test recipient."""
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.management.base import BaseCommand, CommandError
from django.core.validators import validate_email


class Command(BaseCommand):
    help = 'Send a synthetic Brevo HTTPS test message to --to; no clinical data.'

    def add_arguments(self, parser):
        parser.add_argument('--to', required=True, help='An email address controlled by the operator.')

    def handle(self, *args, **options):
        if settings.EMAIL_BACKEND != 'anymail.backends.brevo.EmailBackend':
            raise CommandError('El backend activo no es Brevo. Configura EMAIL_PROVIDER y, en local, DEV_EMAIL_DELIVERY.')
        try:
            validate_email(options['to'])
        except ValidationError:
            raise CommandError('Destinatario inválido.') from None
        try:
            sent = send_mail(
                'Prueba de correo de SmileManager',
                'Este mensaje sintético verifica el envío de correo de SmileManager. No contiene datos clínicos.',
                settings.DEFAULT_FROM_EMAIL,
                [options['to']],
                html_message='<p>Este mensaje sintético verifica el envío de correo de <strong>SmileManager</strong>. No contiene datos clínicos.</p>',
                fail_silently=False,
            )
            if sent != 1:
                raise ValueError('Message was not accepted')
        except Exception:
            raise CommandError('Brevo no aceptó el envío. Revisa la configuración y los logs del proveedor; no compartas las claves.') from None
        self.stdout.write(self.style.SUCCESS('Brevo aceptó la solicitud. Confirma recepción en la bandeja y revisa los eventos de entrega en Brevo.'))

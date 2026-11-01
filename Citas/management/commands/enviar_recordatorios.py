from django.core.management.base import BaseCommand
from Citas.services import send_appointment_reminders


class Command(BaseCommand):
    help = 'Enviar recordatorios de citas 24 horas antes'

    def handle(self, *args, **kwargs):
        result=send_appointment_reminders(write=self.stdout.write)
        self.stdout.write(f"\nCitas encontradas: {result['found']}")
        self.stdout.write(f"Correos enviados: {result['sent']}")
        if result['errors']>0: self.stdout.write(f"Errores: {result['errors']}")

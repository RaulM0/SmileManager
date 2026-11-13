from django.core.management.base import BaseCommand, CommandError
from Citas.services import send_appointment_reminders


class Command(BaseCommand):
    help = 'Enviar recordatorios de citas 24 horas antes'

    def add_arguments(self, parser):
        parser.add_argument('--clinic-id', required=True, help='UUID de la clínica')
        parser.add_argument('--send', action='store_true', help='Enviar; sin esta opción solo se cuentan candidatos')

    def handle(self, *args, **kwargs):
        try:
            result=send_appointment_reminders(clinic_id=kwargs['clinic_id'], dry_run=not kwargs['send'], write=self.stdout.write)
        except ValueError as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write('ENVÍO' if kwargs['send'] else 'SIMULACIÓN')
        self.stdout.write(f"\nCitas encontradas: {result['found']}")
        self.stdout.write(f"Correos enviados: {result['sent']}")
        if result['errors']>0: self.stdout.write(f"Errores: {result['errors']}")

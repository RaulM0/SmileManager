import os

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.utils import timezone
from DiagnosticosIA.models import AIAnalysisRun
from Pacientes.models import Paciente, Consulta
import uuid
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Creates the isolated browser-test account.'

    def handle(self, *args, **options):
        if os.environ.get('DJANGO_SETTINGS_MODULE') != 'SmileManager.settings_e2e':
            raise CommandError('prepare_e2e only runs with SmileManager.settings_e2e')
        for username in ('e2e_doctor', 'e2e_other_doctor', 'e2e_system_admin'):
            user, _ = get_user_model().objects.get_or_create(username=username)
            user.set_password('e2e_password_123')
            user.save()
            if username == 'e2e_system_admin':
                user.user_permissions.add(Permission.objects.get(content_type__app_label='Usuarios', codename='access_system_backoffice'))
                AIAnalysisRun.objects.get_or_create(image_reference=987654321, requested_by=user, defaults={'started_at': timezone.now(), 'status': 'SUCCEEDED', 'model_name': 'synthetic', 'model_version': 'a' * 64, 'input_hash': 'b' * 64, 'request_id': uuid.uuid4()})
        doctor = get_user_model().objects.get(username='e2e_other_doctor')
        patient, _ = Paciente.objects.get_or_create(medico=doctor, email='backoffice-synthetic@example.test', defaults={'nombre': 'PacienteSintetico', 'appat': 'Prueba', 'apmat': 'Demo', 'fecha_nacimiento': '1990-01-01', 'genero': 'F', 'telefono': '5550001122'})
        Consulta.objects.get_or_create(paciente=patient, medico=doctor, motivo_consulta='Consulta sintética', defaults={'fecha_consulta': timezone.now()})
        self.stdout.write(self.style.SUCCESS('E2E accounts ready'))

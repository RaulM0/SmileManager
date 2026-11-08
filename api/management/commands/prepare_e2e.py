import os

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.utils import timezone
from DiagnosticosIA.models import AIAnalysisRun
from Pacientes.models import Paciente, Consulta
from Usuarios.models import Clinic, ClinicMembership, PlatformAdmin
import uuid
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Creates the isolated browser-test account.'

    def handle(self, *args, **options):
        if os.environ.get('DJANGO_SETTINGS_MODULE') != 'SmileManager.settings_e2e':
            raise CommandError('prepare_e2e only runs with SmileManager.settings_e2e')
        primary, _ = Clinic.objects.get_or_create(slug='e2e-primary', defaults={'name': 'Clínica E2E Principal', 'status': 'ACTIVE'})
        for username in ('e2e_doctor', 'e2e_other_doctor', 'e2e_system_admin'):
            user, _ = get_user_model().objects.get_or_create(username=username)
            user.set_password('e2e_password_123')
            user.email = f'{username}@example.test'
            user.save()
            if username in ('e2e_doctor', 'e2e_other_doctor'):
                ClinicMembership.objects.get_or_create(clinic=primary, user=user, defaults={'role': 'DOCTOR', 'status': 'ACTIVE', 'joined_at': timezone.now()})
            if username == 'e2e_system_admin':
                user.user_permissions.add(Permission.objects.get(content_type__app_label='Usuarios', codename='access_system_backoffice'))
                AIAnalysisRun.objects.get_or_create(image_reference=987654321, requested_by=user, defaults={'started_at': timezone.now(), 'status': 'SUCCEEDED', 'model_name': 'synthetic', 'model_version': 'a' * 64, 'input_hash': 'b' * 64, 'request_id': uuid.uuid4()})
        doctor = get_user_model().objects.get(username='e2e_other_doctor')
        patient, _ = Paciente.objects.get_or_create(clinic=primary, medico=doctor, email='backoffice-synthetic@example.test', defaults={'nombre': 'PacienteSintetico', 'appat': 'Prueba', 'apmat': 'Demo', 'fecha_nacimiento': '1990-01-01', 'genero': 'F', 'telefono': '5550001122'})
        Consulta.objects.get_or_create(paciente=patient, medico=doctor, motivo_consulta='Consulta sintética', defaults={'fecha_consulta': timezone.now()})
        tenant_doctor, _ = get_user_model().objects.get_or_create(username='e2e_tenant_doctor')
        tenant_admin, _ = get_user_model().objects.get_or_create(username='e2e_tenant_admin')
        tenant_staff, _ = get_user_model().objects.get_or_create(username='e2e_tenant_staff')
        for account in (tenant_doctor, tenant_admin, tenant_staff):
            account.set_password('e2e_password_123')
            account.save()
        platform, _ = get_user_model().objects.get_or_create(username='e2e_platform_admin')
        platform.set_password('e2e_password_123')
        platform.save()
        PlatformAdmin.objects.update_or_create(user=platform, defaults={'is_active': True})
        for index, label in enumerate(('A', 'B'), 1):
            clinic, _ = Clinic.objects.get_or_create(slug=f'e2e-tenant-{label.lower()}', defaults={'name': f'Clínica E2E {label}', 'status': 'ACTIVE'})
            ClinicMembership.objects.get_or_create(clinic=clinic, user=tenant_doctor, defaults={'role': 'DOCTOR', 'status': 'ACTIVE'})
            ClinicMembership.objects.get_or_create(clinic=clinic, user=tenant_admin, defaults={'role': 'CLINIC_ADMIN', 'status': 'ACTIVE'})
            ClinicMembership.objects.get_or_create(clinic=clinic, user=tenant_staff, defaults={'role': 'STAFF', 'status': 'ACTIVE', 'joined_at': timezone.now()})
            Paciente.objects.get_or_create(clinic=clinic, medico=tenant_doctor, email=f'tenant-{label.lower()}@example.test', defaults={'nombre': f'SINTETICO{label}', 'appat': 'CLINICA', 'apmat': 'PRUEBA', 'fecha_nacimiento': '1990-01-01', 'genero': 'F', 'telefono': f'555000000{index}'})
        self.stdout.write(self.style.SUCCESS('E2E accounts ready'))

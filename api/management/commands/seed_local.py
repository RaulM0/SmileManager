import os

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from Usuarios.models import Clinic, ClinicMembership, PlatformAdmin


class Command(BaseCommand):
    help = 'Crea tres cuentas y una clínica de demostración en el entorno local.'

    @transaction.atomic
    def handle(self, *args, **options):
        if os.environ.get('DJANGO_SETTINGS_MODULE') != 'SmileManager.settings_local':
            raise CommandError('seed_local solo se permite con SmileManager.settings_local.')

        clinic, _ = Clinic.objects.update_or_create(
            slug='smile-demo',
            defaults={'name': 'Clínica Smile Demo', 'status': Clinic.Status.ACTIVE},
        )
        accounts = (
            ('smile', 'Administrador', None),
            ('admin_clinica', 'Administrador de clínica', ClinicMembership.Role.CLINIC_ADMIN),
            ('medico', 'Médico Demo', ClinicMembership.Role.DOCTOR),
        )
        for username, name, role in accounts:
            user, created = get_user_model().objects.get_or_create(
                username=username,
                defaults={'email': f'{username}@example.test', 'first_name': name, 'is_active': True},
            )
            if created:
                user.set_password('Admin123')
                user.save(update_fields=['password'])
            if role is None:
                PlatformAdmin.objects.update_or_create(user=user, defaults={'is_active': True})
                user.user_permissions.add(Permission.objects.get(
                    content_type__app_label='Usuarios', codename='access_system_backoffice',
                ))
            else:
                ClinicMembership.objects.update_or_create(
                    clinic=clinic, user=user,
                    defaults={'role': role, 'status': ClinicMembership.Status.ACTIVE,
                              'joined_at': timezone.now()},
                )
            self.stdout.write(f'{username}: {"creado" if created else "existente"}')
        self.stdout.write(self.style.SUCCESS('Seed local listo. Contraseña inicial: Admin123.'))

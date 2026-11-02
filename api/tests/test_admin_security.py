from django.contrib import admin
from django.contrib.auth.models import Permission, User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
import uuid

from Citas.models import Cita
from DiagnosticosIA.models import AIAnalysisRun
from Pacientes.models import (Paciente, AntescedentesMedicos, Odontograma, Consulta,
    ImagenesClinicas, Consentimiento, EstudioComparativo, ClinicalRevision)
from Usuarios.models import AuditEvent
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken


class ClinicalAdminSecurityTests(TestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser('admin-test', password='test-password')
        self.staff = User.objects.create_user('staff-test', is_staff=True, password='test-password')
        patient = Paciente.objects.create(nombre='A', appat='B', apmat='C', fecha_nacimiento='1990-01-01', genero='F', telefono='1234567890', email='synthetic@example.test', medico=self.superuser)
        self.items = [patient,
            AntescedentesMedicos.objects.create(paciente=patient, medico=self.superuser),
            Odontograma.objects.create(paciente=patient, medico=self.superuser),
            Consulta.objects.create(paciente=patient, medico=self.superuser, fecha_consulta=timezone.now(), motivo_consulta='test'),
            ImagenesClinicas.objects.create(paciente=patient, medico=self.superuser, imagen='synthetic.png', tipo_imagen='RX'),
            Consentimiento.objects.create(paciente=patient, medico=self.superuser, texto='test'),
            EstudioComparativo.objects.create(paciente=patient, medico=self.superuser, fecha_inicio='2026-01-01'),
            Cita.objects.create(paciente=patient, fecha='2030-01-01', hora='10:00', motivo='test')]
        for obj in self.items:
            self.staff.user_permissions.add(Permission.objects.get(content_type__app_label=obj._meta.app_label, codename=f'view_{obj._meta.model_name}'))

    def test_clinical_admin_is_read_only_even_for_superuser(self):
        for user in (self.staff, self.superuser):
            self.client.force_login(user)
            for obj in self.items:
                opts = obj._meta
                with self.subTest(user=user.username, model=opts.model_name):
                    base = f'admin:{opts.app_label}_{opts.model_name}'
                    url = reverse(base + '_change', args=[obj.pk])
                    self.assertEqual(self.client.get(url).status_code, 200)
                    self.assertEqual(self.client.post(url, {}).status_code, 403)
                    self.assertEqual(self.client.post(reverse(base + '_delete', args=[obj.pk]), {}).status_code, 403)
                    self.assertEqual(self.client.post(reverse(base + '_add'), {}).status_code, 403)

    def test_history_not_exposed_and_user_delete_disabled(self):
        self.assertNotIn(AIAnalysisRun, admin.site._registry)
        self.assertNotIn(ClinicalRevision, admin.site._registry)
        self.assertNotIn(OutstandingToken, admin.site._registry)
        self.assertNotIn(BlacklistedToken, admin.site._registry)
        self.client.force_login(self.superuser)
        self.assertEqual(self.client.post(reverse('admin:auth_user_delete', args=[self.staff.pk])).status_code, 403)
        audit = admin.site._registry[AuditEvent]
        request = type('Request', (), {'user': self.superuser})()
        self.assertFalse(audit.has_change_permission(request))
        self.assertFalse(audit.has_delete_permission(request))
        event = AuditEvent.objects.create(actor=self.superuser, action='TEST', resource_type='test', request_id=uuid.uuid4())
        self.staff.user_permissions.add(Permission.objects.get(content_type__app_label='Usuarios', codename='view_auditevent'))
        for user in (self.staff, self.superuser):
            self.client.force_login(user)
            change = reverse('admin:Usuarios_auditevent_change', args=[event.pk])
            self.assertEqual(self.client.get(change).status_code, 200)
            self.assertEqual(self.client.post(change, {}).status_code, 403)
            self.assertEqual(self.client.post(reverse('admin:Usuarios_auditevent_delete', args=[event.pk]), {}).status_code, 403)

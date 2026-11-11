from django.contrib.auth.models import Group, Permission, User
from django.test import TestCase
from django.core.cache import cache
from django.urls import reverse
from rest_framework.test import APIClient
from api.authentication import SessionRefreshToken as RefreshToken
from django.utils import timezone
from DiagnosticosIA.models import AIAnalysisRun
from Citas.models import Cita
from Pacientes.models import Paciente, Consulta, AntescedentesMedicos, ClinicalRevision, Odontograma
import uuid
from unittest.mock import patch

from Usuarios.models import AuditEvent


class BackofficeTests(TestCase):
    def setUp(self):
        cache.clear()
        self.admin = User.objects.create_user('system-admin', password='test')
        self.admin.user_permissions.add(Permission.objects.get(content_type__app_label='Usuarios', codename='access_system_backoffice'))
        self.user = User.objects.create_user('ordinary', password='test')
        self.client = APIClient()

    def test_permission_enforced_all_endpoints(self):
        for name in ('backoffice-dashboard', 'backoffice-users', 'backoffice-audit', 'backoffice-ai-runs', 'backoffice-system'):
            self.client.force_authenticate(None)
            self.assertEqual(self.client.get(reverse(name)).status_code, 401, name)
            self.client.force_authenticate(self.user)
            self.assertEqual(self.client.get(reverse(name)).status_code, 403, name)
            self.client.force_authenticate(self.admin)
            self.assertEqual(self.client.get(reverse(name)).status_code, 200, name)
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.post(reverse('backoffice-user-action', args=[self.admin.pk, 'deactivate'])).status_code, 403)

    def test_create_user_requires_admin_and_audits_without_credentials(self):
        url = reverse('backoffice-user-create')
        payload = {'username': 'synthetic-new', 'email': 'new@example.test', 'password': 'unrelated strong phrase 987!'}
        self.client.force_authenticate(None)
        self.assertEqual(self.client.post(url, payload, format='json').status_code, 401)
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.post(url, payload, format='json').status_code, 403)
        self.client.force_authenticate(self.admin)
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertNotIn('password', response.data)
        created = User.objects.get(username='synthetic-new')
        self.assertTrue(created.check_password(payload['password']))
        self.assertFalse(created.is_staff)
        self.assertFalse(created.is_superuser)
        self.assertTrue(AuditEvent.objects.filter(actor=self.admin, action='USER_CREATED', resource_id=str(created.pk)).exists())
        self.assertFalse(AuditEvent.objects.filter(action__icontains=payload['password']).exists())

    def test_create_user_rejects_extra_privileges_and_validates_password(self):
        self.client.force_authenticate(self.admin)
        url = reverse('backoffice-user-create')
        payload = {'username': 'synthetic-new', 'email': 'new@example.test', 'password': 'unrelated strong phrase 987!', 'is_superuser': True}
        self.assertEqual(self.client.post(url, payload, format='json').status_code, 400)
        del payload['is_superuser']
        self.assertEqual(self.client.post(url, {**payload, 'password': '123'}, format='json').status_code, 400)
        response = self.client.post(url, {**payload, 'backoffice_access': True}, format='json')
        self.assertEqual(response.status_code, 201)
        created = User.objects.get(username='synthetic-new')
        self.assertTrue(created.user_permissions.filter(codename='access_system_backoffice').exists())
        self.assertTrue(AuditEvent.objects.filter(actor=self.admin, action='BACKOFFICE_ACCESS_GRANTED', resource_id=str(created.pk)).exists())
        self.assertEqual(self.client.post(url, payload, format='json').status_code, 400)

    def test_create_user_audit_failure_rolls_back(self):
        self.client.force_authenticate(self.admin)
        self.client.raise_request_exception = False
        with patch('api.services.backoffice.AuditEvent.objects.create', side_effect=RuntimeError('synthetic')):
            response = self.client.post(reverse('backoffice-user-create'), {'username': 'rollback-user', 'email': 'rollback@example.test', 'password': 'unrelated strong phrase 987!'}, format='json')
        self.assertEqual(response.status_code, 500)
        self.assertFalse(User.objects.filter(username='rollback-user').exists())

    def test_activation_is_explicit_audited_and_protects_admins(self):
        old_refresh = str(RefreshToken.for_user(self.user))
        self.client.force_authenticate(self.admin)
        url = reverse('backoffice-user-action', args=[self.user.pk, 'deactivate'])
        self.assertEqual(self.client.post(url).status_code, 200)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
        self.assertTrue(AuditEvent.objects.filter(actor=self.admin, action='USER_DEACTIVATED', resource_id=str(self.user.pk)).exists())
        self.assertEqual(self.client.post(reverse('backoffice-user-action', args=[self.user.pk, 'activate'])).status_code, 200)
        self.assertTrue(AuditEvent.objects.filter(actor=self.admin, action='USER_ACTIVATED').exists())
        self.client.force_authenticate(None)
        self.client.cookies['smile_refresh'] = old_refresh
        self.assertEqual(self.client.post(reverse('api-refresh')).status_code, 401)
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.post(reverse('backoffice-user-action', args=[self.admin.pk, 'deactivate'])).status_code, 409)
        another_admin = User.objects.create_user('another-system-admin')
        another_admin.user_permissions.add(Permission.objects.get(content_type__app_label='Usuarios', codename='access_system_backoffice'))
        self.assertEqual(self.client.post(reverse('backoffice-user-action', args=[another_admin.pk, 'deactivate'])).status_code, 409)
        another_admin.is_active = False
        another_admin.save(update_fields=['is_active'])
        self.assertEqual(self.client.post(reverse('backoffice-user-action', args=[another_admin.pk, 'activate'])).status_code, 409)
        staff = User.objects.create_user('inactive-staff', is_staff=True, is_active=False)
        self.assertEqual(self.client.post(reverse('backoffice-user-action', args=[staff.pk, 'activate'])).status_code, 409)
        self.assertFalse(AuditEvent.objects.filter(action='USER_DEACTIVATED', resource_id=str(self.admin.pk)).exists())
        self.assertEqual(self.client.patch(reverse('backoffice-user', args=[self.user.pk]), {'is_superuser': True}).status_code, 405)

    def test_paginated_minimal_read_only_endpoints_and_filters(self):
        self.client.force_authenticate(self.admin)
        for i in range(25):
            User.objects.create_user('synthetic-%02d' % i)
        users = self.client.get(reverse('backoffice-users'), {'page_size': 2, 'search': 'synthetic-'})
        self.assertEqual(users.data['count'], 25)
        self.assertEqual(len(users.data['results']), 2)
        self.assertNotIn('password', users.data['results'][0])
        self.assertNotIn('is_superuser', users.data['results'][0])
        for name in ('backoffice-audit', 'backoffice-ai-runs'):
            self.assertIn('results', self.client.get(reverse(name)).data)
            self.assertEqual(self.client.post(reverse(name), {}).status_code, 405)
        self.assertEqual(self.client.get(reverse('backoffice-audit'), {'request_id': 'invalid'}).status_code, 400)

    def test_dashboard_query_bound(self):
        self.client.force_authenticate(self.admin)
        with self.assertNumQueries(6):
            self.assertEqual(self.client.get(reverse('backoffice-dashboard')).status_code, 200)

    def test_superuser_requires_explicit_product_permission(self):
        root = User.objects.create_superuser('technical-root', password='test')
        self.client.force_authenticate(root)
        self.assertEqual(self.client.get(reverse('backoffice-dashboard')).status_code, 403)
        root.user_permissions.add(Permission.objects.get(content_type__app_label='Usuarios', codename='access_system_backoffice'))
        self.assertEqual(self.client.get(reverse('backoffice-dashboard')).status_code, 200)

    def test_group_permission_grants_access(self):
        group = Group.objects.create(name='backoffice-synthetic')
        group.permissions.add(Permission.objects.get(content_type__app_label='Usuarios', codename='access_system_backoffice'))
        self.user.groups.add(group)
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.get(reverse('backoffice-dashboard')).status_code, 200)

    def test_login_returns_capability_from_backend(self):
        login = self.client.post(reverse('api-login'), {'username': 'system-admin', 'password': 'test'}, format='json')
        self.assertTrue(login.data['mfa_required'])
        self.assertNotIn('access', login.data)
        setup = self.client.post(reverse('auth-mfa-setup'), {'challenge': login.data['challenge']}, format='json')
        from api.services.mfa import totp
        import time
        verified = self.client.post(reverse('auth-mfa-verify'), {'challenge': login.data['challenge'], 'code': totp(setup.data['secret'], int(time.time()) // 30)}, format='json')
        self.assertTrue(verified.data['user']['can_access_backoffice'])
        normal = self.client.post(reverse('api-login'), {'username': 'ordinary', 'password': 'test'}, format='json')
        self.assertFalse(normal.data['user']['can_access_backoffice'])

    def test_backoffice_permission_does_not_grant_clinical_access(self):
        patient = Paciente.objects.create(nombre='A', appat='B', apmat='C', fecha_nacimiento='1990-01-01', genero='F', telefono='1234567890', email='test@example.test', medico=self.user)
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.get(reverse('api-patient-detail', args=[patient.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse('api-medical-history', args=[patient.pk])).status_code, 404)

    def test_audit_failure_rolls_back_status_change(self):
        self.client.force_authenticate(self.admin)
        self.client.raise_request_exception = False
        with patch('api.services.backoffice.AuditEvent.objects.create', side_effect=RuntimeError('synthetic failure')):
            response = self.client.post(reverse('backoffice-user-action', args=[self.user.pk, 'deactivate']))
        self.assertEqual(response.status_code, 500)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)

    def test_audit_and_ai_are_paginated_filtered_and_read_only(self):
        self.client.force_authenticate(self.admin)
        for i in range(25):
            AuditEvent.objects.create(actor=self.admin, action='USER_ACTIVATED', resource_type='user', resource_id=str(i), request_id=uuid.uuid4())
            AIAnalysisRun.objects.create(image_reference=i, requested_by=self.admin, started_at=timezone.now(), status='SUCCEEDED', model_name='test', model_version='a'*64, input_hash='b'*64, request_id=uuid.uuid4())
        events = self.client.get(reverse('backoffice-audit'), {'action': 'USER_ACTIVATED', 'page_size': 3})
        self.assertEqual(events.data['count'], 25)
        self.assertEqual(len(events.data['results']), 3)
        runs = self.client.get(reverse('backoffice-ai-runs'), {'status': 'SUCCEEDED', 'page_size': 4})
        self.assertEqual(runs.data['count'], 25)
        self.assertEqual(len(runs.data['results']), 4)
        self.assertNotIn('input_hash', runs.data['results'][0])
        self.assertNotIn('detections', runs.data['results'][0])
        self.assertEqual(self.client.patch(reverse('backoffice-ai-run', args=[runs.data['results'][0]['id']]), {'status': 'FAILED'}).status_code, 405)
        self.assertEqual(self.client.delete(reverse('backoffice-audit-detail', args=[events.data['results'][0]['id']])).status_code, 405)

    def test_global_audit_does_not_expose_historical_clinical_events(self):
        event = AuditEvent.objects.create(actor=self.user, action='PATIENT_VIEWED', resource_type='patient', resource_id='12345', request_id=uuid.uuid4())
        self.client.force_authenticate(self.admin)
        response = self.client.get(reverse('backoffice-audit'), {'action': 'PATIENT_VIEWED'})
        self.assertEqual(response.data['count'], 0)
        self.assertEqual(self.client.get(reverse('backoffice-audit-detail', args=[event.pk])).status_code, 404)

    def test_global_clinical_views_are_denied_even_for_backoffice_admin(self):
        patient = Paciente.objects.create(nombre='Sintetico', appat='Prueba', apmat='Demo', fecha_nacimiento='1990-01-01', genero='F', telefono='1234567890', email='synthetic@example.test', medico=self.user)
        Consulta.objects.create(paciente=patient, medico=self.user, fecha_consulta=timezone.now(), motivo_consulta='sintetico')
        AntescedentesMedicos.objects.create(paciente=patient, medico=self.user, alergias='sintetico')
        paths = [reverse('backoffice-patients'), reverse('backoffice-patient', args=[patient.pk]), reverse('backoffice-patient-section', args=[patient.pk, 'history']), reverse('backoffice-appointments')]
        for path in paths:
            self.client.force_authenticate(None)
            self.assertEqual(self.client.get(path).status_code, 401)
            self.client.force_authenticate(self.user)
            self.assertEqual(self.client.get(path).status_code, 403)
            self.client.force_authenticate(self.admin)
            self.assertEqual(self.client.get(path).status_code, 403)
            self.assertEqual(self.client.patch(path, {'is_superuser': True, 'password': 'test'}).status_code, 403)
        for section in ('history', 'consultations', 'odontogram', 'images', 'studies', 'consents', 'revisions', 'ai'):
            response = self.client.get(reverse('backoffice-patient-section', args=[patient.pk, section]))
            self.assertEqual(response.status_code, 403, section)

    def test_superuser_with_backoffice_assignment_cannot_read_global_clinical_data(self):
        root = User.objects.create_superuser('clinical-root', password='test')
        root.user_permissions.add(Permission.objects.get(content_type__app_label='Usuarios', codename='access_system_backoffice'))
        self.client.force_authenticate(root)
        self.assertEqual(self.client.get(reverse('backoffice-patients')).status_code, 403)
        self.assertEqual(self.client.get(reverse('backoffice-appointments')).status_code, 403)
        self.assertTrue(AuditEvent.objects.filter(actor=root, action='BACKOFFICE_CLINICAL_ACCESS_DENIED', outcome='failure').exists())

    def test_inconsistent_clinical_relationship_is_not_exposed(self):
        patient = Paciente.objects.create(nombre='Sintetico', appat='Prueba', apmat='Demo', fecha_nacimiento='1990-01-01', genero='F', telefono='1234567890', email='synthetic@example.test', medico=self.user)
        AntescedentesMedicos.objects.create(paciente=patient, medico=self.admin, alergias='no revelar')
        self.client.force_authenticate(self.admin)
        response = self.client.get(reverse('backoffice-patient-section', args=[patient.pk, 'history']))
        self.assertEqual(response.status_code, 403)

    def test_global_lists_have_bounded_queries(self):
        for index in range(12):
            patient = Paciente.objects.create(nombre='Sintetico', appat='Prueba', apmat='Demo', fecha_nacimiento='1990-01-01', genero='F', telefono=f'{index:010}', email=f'synthetic{index}@example.test', medico=self.user)
            Cita.objects.create(paciente=patient, fecha='2026-01-01', hora='10:00', motivo='sintetico')
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.get(reverse('backoffice-patients')).status_code, 403)
        self.assertEqual(self.client.get(reverse('backoffice-appointments')).status_code, 403)

    def test_global_clinical_writes_remain_denied_after_integration(self):
        patient = Paciente.objects.create(nombre='A', appat='B', apmat='C', fecha_nacimiento='1990-01-01', genero='F', telefono='1234567890', email='blocked@example.test', medico=self.user)
        appointment = Cita.objects.create(paciente=patient, fecha='2030-01-01', hora='10:00', motivo='synthetic')
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.patch(reverse('backoffice-patient', args=[patient.pk]), {'nombre': 'Changed'}, format='json').status_code, 403)
        for record in ('medical-history', 'odontogram'):
            url = reverse('backoffice-patient-record', args=[patient.pk, record])
            self.assertEqual(self.client.get(url).status_code, 403)
            self.assertEqual(self.client.put(url, {'version': 0}, format='json').status_code, 403)
        for operation in ('complete', 'cancel'):
            url = reverse('backoffice-appointment-transition', args=[appointment.pk, operation])
            self.assertEqual(self.client.post(url, {}, format='json').status_code, 403)
        patient.refresh_from_db()
        appointment.refresh_from_db()
        self.assertEqual(patient.nombre, 'A')
        self.assertEqual(appointment.estatus, 'P')
        self.assertFalse(AntescedentesMedicos.objects.filter(paciente=patient).exists())
        self.assertFalse(Odontograma.objects.filter(paciente=patient).exists())
        self.assertFalse(ClinicalRevision.objects.filter(patient=patient).exists())

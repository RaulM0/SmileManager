import io
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, TransactionTestCase, override_settings
from django.urls import reverse
from openpyxl import load_workbook
from PIL import Image
from rest_framework.test import APIClient

from Pacientes.access import scoped
from api.services.exports import excel_response
from api.throttles import AccountThrottle, ExpensiveThrottle, ExportThrottle
from api.upload_policy import validate_upload
from Pacientes.models import Consulta, ImagenesClinicas, Paciente
from Usuarios.models import AuditEvent
from Citas.models import Cita


def image_upload(name='test.png', size=(2, 2), mime='image/png'):
    data = io.BytesIO()
    Image.new('RGB', size).save(data, format='PNG')
    return SimpleUploadedFile(name, data.getvalue(), content_type=mime)


class FoundationTests(TestCase):
    def setUp(self):
        cache.clear()
        self.a = User.objects.create_user('foundation-a', password='test-password')
        self.b = User.objects.create_user('foundation-b', password='test-password')
        self.patient = Paciente.objects.create(nombre='A', appat='A', apmat='A', fecha_nacimiento='1990-01-01', genero='F', telefono='1000000000', email='a@sample.test', medico=self.a)
        self.foreign = Paciente.objects.create(nombre='B', appat='B', apmat='B', fecha_nacimiento='1990-01-01', genero='F', telefono='2000000000', email='b@sample.test', medico=self.b)
        self.client = APIClient()
        self.client.force_authenticate(self.a)

    def test_inconsistent_clinical_rows_fail_closed(self):
        consultation = Consulta.objects.create(paciente=self.foreign, medico=self.a, fecha_consulta='2026-01-01T00:00:00Z', motivo_consulta='x')
        image = ImagenesClinicas.objects.create(paciente=self.foreign, medico=self.a, consulta=consultation, tipo_imagen='x', imagen='fake.png')
        self.assertFalse(scoped(self.a, Consulta).filter(pk=consultation.pk).exists())
        self.assertFalse(scoped(self.a, ImagenesClinicas).filter(pk=image.pk).exists())
        self.assertEqual(self.client.get(reverse('api-consultation-detail', args=[consultation.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse('api-clinical-image-detail', args=[image.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse('api-clinical-image-analyze', args=[image.pk])).status_code, 404)
        self.assertFalse(AuditEvent.objects.filter(action='AI_ANALYSIS_REQUESTED').exists())
        mismatched = ImagenesClinicas.objects.create(paciente=self.patient, medico=self.b, tipo_imagen='x', imagen='fake.png')
        self.assertEqual(self.client.get(reverse('api-clinical-image-file', args=[mismatched.pk])).status_code, 404)
        self.client.force_authenticate(self.b)
        self.assertEqual(self.client.get(reverse('api-clinical-image-file', args=[mismatched.pk])).status_code, 404)

    def test_cross_owner_resource_matrix(self):
        appointment = Cita.objects.create(paciente=self.foreign, fecha='2030-01-01', hora='10:00', motivo='x')
        targets = [
            ('api-patient-detail', self.foreign.pk, ('get', 'put', 'patch')),
            ('api-appointment-detail', appointment.pk, ('get', 'put', 'patch')),
            ('api-appointment-complete', appointment.pk, ('post',)),
            ('api-appointment-cancel', appointment.pk, ('post',)),
            ('api-medical-history', self.foreign.pk, ('get', 'put')),
            ('api-consultations', self.foreign.pk, ('get', 'post')),
            ('api-clinical-images', self.foreign.pk, ('get', 'post')),
            ('api-odontogram', self.foreign.pk, ('get', 'put')),
            ('api-comparative-study', self.foreign.pk, ('get', 'put')),
            ('api-consent', self.foreign.pk, ('get', 'post')),
            ('api-patient-email', self.foreign.pk, ('post',)),
        ]
        for name, pk, methods in targets:
            for method in methods:
                with self.subTest(route=name, method=method):
                    response = getattr(self.client, method)(reverse(name, args=[pk]), {}, format='json')
                    self.assertEqual(response.status_code, 404)
        self.client.force_authenticate(None)
        self.assertIn(self.client.get(reverse('api-patient-detail', args=[self.patient.pk])).status_code, (401, 403))

    def test_authentication_audit_has_no_credentials(self):
        self.client.force_authenticate(None)
        url = reverse('api-login')
        self.assertEqual(self.client.post(url, {'username': 'foundation-a', 'password': 'wrong'}, format='json').status_code, 400)
        self.assertTrue(AuditEvent.objects.filter(action='AUTH_LOGIN_FAILED', outcome='failure', actor__isnull=True).exists())
        self.assertEqual(self.client.post(url, {'username': 'foundation-a', 'password': 'test-password'}, format='json').status_code, 200)
        self.assertTrue(AuditEvent.objects.filter(action='AUTH_LOGIN_SUCCESS', actor=self.a).exists())
        self.assertEqual(self.client.post(reverse('api-logout')).status_code, 204)
        self.assertTrue(AuditEvent.objects.filter(action='AUTH_LOGOUT', actor=self.a).exists())

    def test_reused_refresh_and_access_after_logout_are_rejected(self):
        self.client.force_authenticate(None)
        logged_in = self.client.post(reverse('api-login'), {'username': 'foundation-a', 'password': 'test-password'}, format='json')
        access = logged_in.data['access']
        old_refresh = self.client.cookies['smile_refresh'].value
        self.assertEqual(self.client.post(reverse('api-refresh')).status_code, 200)
        rotated_refresh = self.client.cookies['smile_refresh'].value
        self.client.cookies['smile_refresh'] = old_refresh
        self.assertEqual(self.client.post(reverse('api-refresh')).status_code, 401)
        self.client.cookies['smile_refresh'] = rotated_refresh
        self.assertEqual(self.client.post(reverse('api-logout')).status_code, 204)
        # Logout revokes the server session, including previously issued access.
        self.assertEqual(self.client.get(reverse('api-patient-detail', args=[self.patient.pk]), HTTP_AUTHORIZATION='Bearer ' + access).status_code, 401)

    def test_failed_audit_insert_rolls_back_clinical_update(self):
        self.client.raise_request_exception = False
        with patch('api.audit.AuditEvent.objects.create', side_effect=RuntimeError('test failure')):
            response = self.client.patch(reverse('api-patient-detail', args=[self.patient.pk]), {'nombre': 'CAMBIADO'}, format='json')
        self.assertEqual(response.status_code, 500)
        self.patient.refresh_from_db()
        self.assertEqual(self.patient.nombre, 'A')

    def test_audit_success_and_rejected_access(self):
        self.assertEqual(self.client.get(reverse('api-patient-detail', args=[self.patient.pk])).status_code, 200)
        event = AuditEvent.objects.get(action='PATIENT_VIEW')
        self.assertEqual(event.actor, self.a)
        self.assertEqual(event.resource_id, str(self.patient.pk))
        self.assertEqual(self.client.get(reverse('api-patient-detail', args=[self.foreign.pk])).status_code, 404)
        self.assertEqual(AuditEvent.objects.filter(action='PATIENT_VIEW').count(), 1)
        self.assertEqual(self.client.get(reverse('api-export-patients')).status_code, 200)
        self.assertTrue(AuditEvent.objects.filter(action='CLINICAL_EXPORT', actor=self.a).exists())

    def test_upload_validation_rejects_invalid_before_save(self):
        validate_upload(image_upload())
        for upload in (SimpleUploadedFile('bad.png', b'not an image', content_type='image/png'), image_upload('wrong.jpg'), image_upload(mime='image/jpeg'), SimpleUploadedFile('empty.png', b'', content_type='image/png')):
            with self.subTest(name=upload.name), self.assertRaises(ValidationError):
                validate_upload(upload)
        with override_settings(CLINICAL_UPLOAD_MAX_PIXELS=3):
            with self.assertRaises(ValidationError): validate_upload(image_upload())
        with override_settings(CLINICAL_UPLOAD_MAX_BYTES=5):
            with self.assertRaises(ValidationError): validate_upload(image_upload())

    def test_excel_cells_do_not_become_formulas(self):
        response = excel_response([{'a': '=1+1', 'b': '+x', 'c': '-x', 'd': '@x', 'n': -2}], filename='x.xlsx', sheet='x')
        sheet = load_workbook(io.BytesIO(response.content), data_only=False).active
        for cell in list(sheet.rows)[1][:4]:
            self.assertEqual(cell.data_type, 's')
            self.assertTrue(cell.value.startswith("'"))
        self.assertEqual(sheet['E2'].value, -2)

    @patch('DiagnosticosIA.runs.model_version', return_value='a' * 64)
    def test_expensive_throttle_is_independent(self, _version):
        image = ImagenesClinicas.objects.create(paciente=self.patient, medico=self.a, tipo_imagen='x', imagen=SimpleUploadedFile('test.bin', b'synthetic'))
        url = reverse('api-clinical-image-analyze', args=[image.pk])
        with patch.object(ExpensiveThrottle, 'rate', '1/min', create=True), patch('api.legacy_views.analyze_clinical_image', return_value=[]):
            self.assertEqual(self.client.post(url).status_code, 200)
            self.assertEqual(self.client.post(url).status_code, 429)
            self.assertEqual(self.client.get(reverse('api-patient-detail', args=[self.patient.pk])).status_code, 200)

    def test_login_and_export_limits(self):
        with patch.object(ExportThrottle, 'rate', '1/min', create=True):
            self.assertEqual(self.client.get(reverse('api-export-patients')).status_code, 200)
            self.assertEqual(self.client.get(reverse('api-export-patients')).status_code, 429)
        self.client.force_authenticate(None)
        with patch.object(AccountThrottle, 'rate', '1/min', create=True):
            data = {'username': 'unknown', 'password': 'incorrect'}
            self.assertEqual(self.client.post(reverse('api-login'), data, format='json').status_code, 400)
            self.assertEqual(self.client.post(reverse('api-login'), data, format='json').status_code, 429)



class StreamingAuditTests(TransactionTestCase):
    def test_image_download_is_audited(self):
        user = User.objects.create_user('streaming-audit')
        patient = Paciente.objects.create(nombre='A', appat='A', apmat='A', fecha_nacimiento='1990-01-01', genero='F', telefono='1000000000', email='a@sample.test', medico=user)
        image = ImagenesClinicas.objects.create(paciente=patient, medico=user, tipo_imagen='x', imagen=image_upload())
        client = APIClient()
        client.force_authenticate(user)
        response = client.get(reverse('api-clinical-image-file', args=[image.pk]))
        self.assertEqual(response.status_code, 200)
        response.close()
        event = AuditEvent.objects.get(action='CLINICAL_IMAGE_VIEW')
        self.assertEqual((event.actor_id, event.resource_id), (user.pk, str(image.pk)))

import json
import os
import subprocess
import sys
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, SimpleTestCase, TestCase
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken

from Citas.models import Cita
from Pacientes.models import Consentimiento, EstudioComparativo, ImagenesClinicas, Odontograma, Paciente


class ProductionConfigurationTests(SimpleTestCase):
    def test_production_requires_secret_and_explicit_hosts(self):
        env = os.environ.copy()
        env.update(DJANGO_SETTINGS_MODULE='SmileManager.settings', DJANGO_DEBUG='False', DATABASE_URL='sqlite:///:memory:', AWS_STORAGE_BUCKET_NAME='example-invalid', PYTHONDONTWRITEBYTECODE='1')
        for key in ('SECRET_KEY', 'ALLOWED_HOSTS'):
            env.pop(key, None)
        command = [sys.executable, '-B', '-c', 'import SmileManager.settings']
        self.assertNotEqual(subprocess.run(command, env=env, capture_output=True).returncode, 0)
        env['SECRET_KEY'] = 'isolated-test-secret-only-012345678901234567890123456789'
        env['ALLOWED_HOSTS'] = '*'
        self.assertNotEqual(subprocess.run(command, env=env, capture_output=True).returncode, 0)
        env['ALLOWED_HOSTS'] = 'example.invalid'
        self.assertEqual(subprocess.run(command, env=env, capture_output=True).returncode, 0)


class PhaseZeroTests(TestCase):
    def setUp(self):
        cache.clear()
        self.owner = User.objects.create_user(username='a', password='safe-test-password')
        self.other = User.objects.create_user(username='b', password='safe-test-password')
        self.patient = Paciente.objects.create(nombre='A', appat='A', apmat='A', fecha_nacimiento='1990-01-01', genero='F', telefono='1111111111', email='a@example.test', medico=self.owner)
        self.foreign = Paciente.objects.create(nombre='B', appat='B', apmat='B', fecha_nacimiento='1990-01-01', genero='F', telefono='2222222222', email='b@example.test', medico=self.other)
        self.client = Client(enforce_csrf_checks=True)
        self.client.force_login(self.owner)

    def token(self):
        self.client.get(reverse('odontograma', args=[self.patient.id]))
        return self.client.cookies['csrftoken'].value

    def test_odontogram_requires_csrf_and_ownership(self):
        url = reverse('guardar_odontograma', args=[self.patient.id])
        payload = json.dumps({'denticion_permanente': {'11': {'oclusal': 'sano'}}, 'denticion_decidua': {}, 'resumen': {}, 'version': 0})
        self.assertEqual(self.client.post(url, payload, content_type='application/json').status_code, 403)
        csrf = self.token()
        foreign_url = reverse('guardar_odontograma', args=[self.foreign.id])
        self.assertEqual(self.client.post(foreign_url, payload, content_type='application/json', HTTP_X_CSRFTOKEN=csrf).status_code, 404)
        self.assertEqual(self.client.post(url, payload, content_type='application/json', HTTP_X_CSRFTOKEN=csrf).status_code, 200)
        self.assertEqual(Odontograma.objects.count(), 1)
        self.client.logout()
        self.assertIn(self.client.post(url, payload, content_type='application/json', HTTP_X_CSRFTOKEN=csrf).status_code, (302, 401, 403))

    def test_appointments_require_post_and_csrf(self):
        appointment = Cita.objects.create(paciente=self.patient, fecha='2030-01-01', hora='10:00', motivo='x')
        for name in ('confirmar_asistencia', 'cancelar_cita'):
            url = reverse(name, args=[appointment.id])
            self.assertEqual(self.client.get(url).status_code, 405)
            self.assertEqual(self.client.post(url).status_code, 403)
        appointment.refresh_from_db()
        self.assertEqual(appointment.estatus, 'P')
        csrf = self.token()
        self.assertEqual(self.client.post(reverse('confirmar_asistencia', args=[appointment.id]), HTTP_X_CSRFTOKEN=csrf).status_code, 302)
        appointment.refresh_from_db()
        self.assertEqual(appointment.estatus, 'C')

    @patch('DiagnosticosIA.views.analyze_clinical_image')
    def test_diagnostic_get_does_not_analyze_post_does(self, analyze):
        image = ImagenesClinicas.objects.create(paciente=self.patient, medico=self.owner, tipo_imagen='RX', imagen=SimpleUploadedFile('test.gif', b'example'))
        url = reverse('resultados', args=[image.id])
        self.assertEqual(self.client.get(url).status_code, 200)
        analyze.assert_not_called()
        self.assertEqual(self.client.post(url).status_code, 403)
        csrf = self.token()
        analyze.return_value = []
        self.assertEqual(self.client.post(url, HTTP_X_CSRFTOKEN=csrf).status_code, 200)
        analyze.assert_called_once()
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.post(url, HTTP_X_CSRFTOKEN=csrf).status_code, 404)

    def test_direct_media_and_foreign_file_are_denied(self):
        image = ImagenesClinicas.objects.create(paciente=self.foreign, medico=self.other, tipo_imagen='RX', imagen=SimpleUploadedFile('test.gif', b'example'))
        direct = '/media/' + image.imagen.name
        self.assertEqual(self.client.get(direct).status_code, 404)
        session_url = reverse('clinical-session-file', args=['image', image.id, 'imagen'])
        self.assertEqual(self.client.get(session_url).status_code, 404)
        self.client.logout()
        self.assertIn(self.client.get(session_url).status_code, (302, 401, 403))
        api_url = reverse('api-clinical-image-file', args=[image.id])
        self.assertIn(self.client.get(api_url).status_code, (401, 403))
        token = RefreshToken.for_user(self.owner).access_token
        self.assertEqual(self.client.get(api_url, HTTP_AUTHORIZATION=f'Bearer {token}').status_code, 404)

    def test_api_exposes_only_authorized_file_routes(self):
        image = ImagenesClinicas.objects.create(paciente=self.patient, medico=self.owner, tipo_imagen='RX', imagen=SimpleUploadedFile('original.gif', b'original'), resultados=SimpleUploadedFile('result.gif', b'result'))
        token = RefreshToken.for_user(self.owner).access_token
        response = self.client.get(reverse('api-clinical-image-detail', args=[image.id]), HTTP_AUTHORIZATION=f'Bearer {token}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['imagen_url'], reverse('api-clinical-image-file', args=[image.id]))
        self.assertEqual(response.json()['resultados_url'], reverse('api-clinical-image-result-file', args=[image.id]))
        self.assertNotIn('resultados', response.json())
        self.assertNotIn('/media/', response.content.decode())

    def test_get_consent_and_history_do_not_create_rows(self):
        self.client.get(reverse('antecedentes', args=[self.patient.id]))
        self.client.get(reverse('consentimiento', args=[self.patient.id]))
        self.assertFalse(Consentimiento.objects.exists())
        from Pacientes.models import AntescedentesMedicos
        self.assertFalse(AntescedentesMedicos.objects.exists())
        token = RefreshToken.for_user(self.owner).access_token
        self.assertEqual(self.client.get(reverse('api-consent', args=[self.patient.id]), HTTP_AUTHORIZATION=f'Bearer {token}').status_code, 200)
        self.assertFalse(Consentimiento.objects.exists())

    def test_private_study_and_consent_files_and_urls(self):
        study = EstudioComparativo.objects.create(paciente=self.foreign, medico=self.other, fecha_inicio='2026-01-01', antes_frontal=SimpleUploadedFile('study.gif', b'private'))
        consent = Consentimiento.objects.create(paciente=self.foreign, medico=self.other, texto='', archivo_ine=SimpleUploadedFile('id.pdf', b'private'), pdf_generado=SimpleUploadedFile('consent.pdf', b'private'))
        session_urls = [reverse('clinical-session-file', args=['study', study.id, 'antes_frontal']), reverse('clinical-session-file', args=['consent', consent.id, 'archivo_ine']), reverse('clinical-session-file', args=['consent', consent.id, 'pdf_generado'])]
        api_urls = [reverse('api-comparative-study-image', args=[self.foreign.id, 'antes_frontal']), reverse('api-consent-file', args=[self.foreign.id]), reverse('api-consent-pdf', args=[self.foreign.id])]
        for url in session_urls:
            self.assertEqual(self.client.get(url).status_code, 404)
        token = RefreshToken.for_user(self.owner).access_token
        for url in api_urls:
            self.assertEqual(self.client.get(url, HTTP_AUTHORIZATION=f'Bearer {token}').status_code, 404)
        self.client.force_login(self.other)
        for url in session_urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(b''.join(response.streaming_content), b'private')
        token = RefreshToken.for_user(self.other).access_token
        for url in api_urls:
            response = self.client.get(url, HTTP_AUTHORIZATION=f'Bearer {token}')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(b''.join(response.streaming_content), b'private')

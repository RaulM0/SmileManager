import json
import os
import subprocess
import sys
from cryptography.fernet import Fernet

from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, SimpleTestCase, TestCase
from django.urls import reverse
from api.authentication import SessionRefreshToken as RefreshToken

from Pacientes.models import AntescedentesMedicos, Consentimiento, EstudioComparativo, ImagenesClinicas, Paciente


class ProductionConfigurationTests(SimpleTestCase):
    def test_production_requires_secret_and_explicit_hosts(self):
        env = os.environ.copy()
        env.update(DJANGO_SETTINGS_MODULE='SmileManager.settings', DJANGO_DEBUG='False', DATABASE_URL='postgresql://test:test@example.invalid/test', AWS_STORAGE_BUCKET_NAME='example-invalid', PYTHONDONTWRITEBYTECODE='1', THROTTLE_REDIS_URL='redis://127.0.0.1:6379/15')
        for key in ('SECRET_KEY', 'ALLOWED_HOSTS'):
            env.pop(key, None)
        command = [sys.executable, '-B', '-c', 'import SmileManager.settings']
        self.assertNotEqual(subprocess.run(command, env=env, capture_output=True).returncode, 0)
        env['SECRET_KEY'] = 'isolated-test-secret-only-012345678901234567890123456789'
        env['ALLOWED_HOSTS'] = '*'
        self.assertNotEqual(subprocess.run(command, env=env, capture_output=True).returncode, 0)
        env['ALLOWED_HOSTS'] = 'example.invalid'
        env['MFA_ENCRYPTION_KEYS'] = Fernet.generate_key().decode()
        env['AUDIT_SIGNING_KEYS'] = __import__('secrets').token_urlsafe(32)
        env['FILE_SCAN_KEYS'] = __import__('secrets').token_urlsafe(32)
        env['DOCUMENT_SEAL_KEYS'] = __import__('secrets').token_urlsafe(32)
        self.assertEqual(subprocess.run(command, env=env, capture_output=True).returncode, 0)
        for setting in ('MFA_ENCRYPTION_KEYS', 'DOCUMENT_SEAL_KEYS', 'AUDIT_SIGNING_KEYS', 'FILE_SCAN_KEYS'):
            previous = env.pop(setting)
            self.assertNotEqual(subprocess.run(command, env=env, capture_output=True).returncode, 0)
            env[setting] = previous
        env['DATABASE_URL'] = 'sqlite:///:memory:'
        self.assertNotEqual(subprocess.run(command, env=env, capture_output=True).returncode, 0)
        env['DATABASE_URL'] = 'postgresql://test:test@example.invalid/test'
        env.pop('THROTTLE_REDIS_URL')
        self.assertNotEqual(subprocess.run(command, env=env, capture_output=True).returncode, 0)
        env['THROTTLE_REDIS_URL'] = 'redis://127.0.0.1:6379/15'
        for proxies in ('0.0.0.0/0', '::/0', 'not-a-network'):
            env['THROTTLE_TRUSTED_PROXIES'] = proxies
            self.assertNotEqual(subprocess.run(command, env=env, capture_output=True).returncode, 0)


class PhaseZeroTests(TestCase):
    def setUp(self):
        cache.clear()
        self.owner = User.objects.create_user(username='a', password='safe-test-password')
        self.other = User.objects.create_user(username='b', password='safe-test-password')
        self.patient = Paciente.objects.create(nombre='A', appat='A', apmat='A', fecha_nacimiento='1990-01-01', genero='F', telefono='1111111111', email='a@example.test', medico=self.owner)
        self.foreign = Paciente.objects.create(nombre='B', appat='B', apmat='B', fecha_nacimiento='1990-01-01', genero='F', telefono='2222222222', email='b@example.test', medico=self.other)
        self.client = Client(enforce_csrf_checks=True)
        self.client.force_login(self.owner)
    def test_unauthenticated_and_foreign_clinical_files_are_denied(self):
        image = ImagenesClinicas.objects.create(paciente=self.foreign, medico=self.other, tipo_imagen='RX', imagen=SimpleUploadedFile('test.gif', b'example'))
        self.assertEqual(self.client.get('/media/' + image.imagen.name).status_code, 404)
        url = reverse('api-clinical-image-file', args=[image.id])
        self.assertEqual(self.client.get(url).status_code, 401)
        token = RefreshToken.for_user(self.owner).access_token
        self.assertEqual(self.client.get(url, HTTP_AUTHORIZATION=f'Bearer {token}').status_code, 404)

    def test_reading_empty_records_does_not_create_data(self):
        token = RefreshToken.for_user(self.owner).access_token
        headers = {'HTTP_AUTHORIZATION': f'Bearer {token}'}
        for name in ('api-medical-history', 'api-consent'):
            self.assertEqual(self.client.get(reverse(name, args=[self.patient.id]), **headers).status_code, 200)
        self.assertFalse(AntescedentesMedicos.objects.exists())
        self.assertFalse(Consentimiento.objects.exists())

    def test_study_and_consent_files_require_owner(self):
        EstudioComparativo.objects.create(paciente=self.foreign, medico=self.other, fecha_inicio='2026-01-01', antes_frontal=SimpleUploadedFile('study.gif', b'private'))
        Consentimiento.objects.create(paciente=self.foreign, medico=self.other, texto='', archivo_ine=SimpleUploadedFile('id.pdf', b'private'), pdf_generado=SimpleUploadedFile('consent.pdf', b'private'))
        urls = [reverse('api-comparative-study-image', args=[self.foreign.id, 'antes_frontal']), reverse('api-consent-file', args=[self.foreign.id]), reverse('api-consent-pdf', args=[self.foreign.id])]
        for user, expected in ((self.owner, 404), (self.other, 200)):
            token = RefreshToken.for_user(user).access_token
            for url in urls:
                response = self.client.get(url, HTTP_AUTHORIZATION=f'Bearer {token}')
                self.assertEqual(response.status_code, expected)
                if expected == 200:
                    self.assertEqual(b''.join(response.streaming_content), b'private')

    def test_api_exposes_only_authorized_file_routes(self):
        image = ImagenesClinicas.objects.create(paciente=self.patient, medico=self.owner, tipo_imagen='RX', imagen=SimpleUploadedFile('original.gif', b'original'), resultados=SimpleUploadedFile('result.gif', b'result'))
        token = RefreshToken.for_user(self.owner).access_token
        response = self.client.get(reverse('api-clinical-image-detail', args=[image.id]), HTTP_AUTHORIZATION=f'Bearer {token}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['imagen_url'], reverse('api-clinical-image-file', args=[image.id]))
        self.assertEqual(response.json()['resultados_url'], reverse('api-clinical-image-result-file', args=[image.id]))
        self.assertNotIn('resultados', response.json())
        self.assertNotIn('/media/', response.content.decode())

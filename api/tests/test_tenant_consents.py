import threading
from concurrent.futures import ThreadPoolExecutor
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import close_old_connections
from django.test import TransactionTestCase, override_settings, skipUnlessDBFeature
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase

from Pacientes.models import Consentimiento, Paciente
from Usuarios.models import AuditEvent, Clinic, ClinicMembership


def pdf():
    return SimpleUploadedFile('identificacion-privada.pdf', b'%PDF-1.4\nsynthetic\n%%EOF', content_type='application/pdf')


class TenantConsentTests(APITestCase):
    def setUp(self):
        media = self.enterContext(TemporaryDirectory())
        self.enterContext(override_settings(MEDIA_ROOT=media))
        self.doctor = User.objects.create_user('tenant-consent-doctor')
        self.a = Clinic.objects.create(name='A', slug='consent-a', status='ACTIVE')
        self.b = Clinic.objects.create(name='B', slug='consent-b', status='ACTIVE')
        self.member = ClinicMembership.objects.create(user=self.doctor, clinic=self.a, role='DOCTOR', status='ACTIVE')
        ClinicMembership.objects.create(user=self.doctor, clinic=self.b, role='DOCTOR', status='ACTIVE')
        self.patient_a = self.patient(self.a, '1111111111')
        self.patient_b = self.patient(self.b, '2222222222')
        self.client.force_authenticate(self.doctor)

    def patient(self, clinic, phone):
        return Paciente.objects.create(nombre='A', appat='B', apmat='C', fecha_nacimiento='2000-01-01', genero='F', telefono=phone, email=f'{phone}@example.test', medico=self.doctor, clinic=clinic)

    def test_accept_once_and_download_is_tenant_scoped(self):
        url = reverse('tenant-consent', args=[self.patient_a.pk])
        response = self.client.post(url, {'texto': 'sintético', 'archivo_ine': pdf()}, format='multipart', HTTP_X_CLINIC_ID=str(self.a.pk))
        self.assertEqual(response.status_code, 200, response.data)
        consent = Consentimiento.objects.get(paciente=self.patient_a)
        self.assertTrue(consent.archivo_ine.name.startswith(f'tenants/{self.a.pk}/patients/{self.patient_a.pk}/consents/identity/'))
        self.assertNotIn('identificacion-privada', consent.archivo_ine.name)
        self.assertEqual(self.client.post(url, {'texto': 'nuevo', 'archivo_ine': pdf()}, format='multipart', HTTP_X_CLINIC_ID=str(self.a.pk)).status_code, 409)
        file_url = reverse('tenant-consent-file', args=[self.patient_a.pk, 'identity'])
        self.assertEqual(self.client.get(file_url, HTTP_X_CLINIC_ID=str(self.b.pk)).status_code, 404)
        response = self.client.get(file_url, HTTP_X_CLINIC_ID=str(self.a.pk))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b''.join(response.streaming_content).startswith(b'%PDF-'))
        self.assertIn('no-store', response['Cache-Control'])
        self.assertTrue(AuditEvent.objects.filter(clinic=self.a, action='TENANT_CONSENT_ACCEPTED').exists())
        self.member.status = 'REVOKED'
        self.member.save(update_fields=['status'])
        self.assertEqual(self.client.get(file_url, HTTP_X_CLINIC_ID=str(self.a.pk)).status_code, 403)

    def test_cross_clinic_and_forged_patient_denied(self):
        foreign = reverse('tenant-consent', args=[self.patient_b.pk])
        self.assertEqual(self.client.post(foreign, {'archivo_ine': pdf()}, format='multipart', HTTP_X_CLINIC_ID=str(self.a.pk)).status_code, 404)
        own = reverse('tenant-consent', args=[self.patient_a.pk])
        self.assertEqual(self.client.post(own, {'archivo_ine': pdf(), 'paciente_id': self.patient_b.pk}, format='multipart', HTTP_X_CLINIC_ID=str(self.a.pk)).status_code, 400)
        self.assertFalse(Consentimiento.objects.exists())

    def test_validation_failure_preserves_existing_file(self):
        existing = Consentimiento.objects.create(paciente=self.patient_a, medico=self.doctor, texto='', archivo_ine=pdf())
        original = existing.archivo_ine.name
        url = reverse('tenant-consent', args=[self.patient_a.pk])
        response = self.client.post(url, {'texto': 'x'*100001, 'archivo_ine': pdf()}, format='multipart', HTTP_X_CLINIC_ID=str(self.a.pk))
        self.assertEqual(response.status_code, 400)
        existing.refresh_from_db()
        self.assertEqual(existing.archivo_ine.name, original)
        self.assertTrue(default_storage.exists(original))

    @patch('api.tenant_patients.AuditEvent.objects.create', side_effect=RuntimeError('synthetic audit failure'))
    def test_failed_audit_rolls_back_and_removes_new_upload(self, _audit):
        self.client.raise_request_exception = False
        url = reverse('tenant-consent', args=[self.patient_a.pk])
        response = self.client.post(url, {'texto': 'sintético', 'archivo_ine': pdf()}, format='multipart', HTTP_X_CLINIC_ID=str(self.a.pk))
        self.assertEqual(response.status_code, 500)
        self.assertFalse(Consentimiento.objects.exists())
        prefix = f'tenants/{self.a.pk}/patients/{self.patient_a.pk}/consents/identity'
        self.assertEqual(default_storage.listdir(prefix)[1], [])


@skipUnlessDBFeature('has_select_for_update')
class TenantConsentConcurrencyTests(TransactionTestCase):
    def test_concurrent_acceptance_creates_only_one_consent(self):
        with TemporaryDirectory() as media, override_settings(MEDIA_ROOT=media):
            doctor = User.objects.create_user('tenant-consent-concurrent')
            clinic = Clinic.objects.create(name='A', slug='consent-concurrent', status='ACTIVE')
            ClinicMembership.objects.create(user=doctor, clinic=clinic, role='DOCTOR', status='ACTIVE')
            patient = Paciente.objects.create(nombre='A', appat='B', apmat='C', fecha_nacimiento='2000-01-01', genero='F', telefono='1234567890', email='consent@example.test', medico=doctor, clinic=clinic)
            barrier = threading.Barrier(2)

            def accept(_):
                close_old_connections()
                try:
                    client = APIClient()
                    client.force_authenticate(doctor)
                    barrier.wait(timeout=10)
                    return client.post(reverse('tenant-consent', args=[patient.pk]), {'texto': 'sintético', 'archivo_ine': pdf()}, format='multipart', HTTP_X_CLINIC_ID=str(clinic.pk)).status_code
                finally:
                    close_old_connections()

            with ThreadPoolExecutor(max_workers=2) as executor:
                statuses = list(executor.map(accept, (0, 1)))
            self.assertCountEqual(statuses, [200, 409])
            self.assertEqual(Consentimiento.objects.filter(paciente=patient).count(), 1)

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

from Pacientes.models import Consentimiento, ConsentEvidence, Paciente
from Usuarios.models import AuditEvent, Clinic, ClinicMembership
from .document_fixtures import publish_documents, evidence_values, signed_pdf_bytes, scan_test_documents


def pdf():
    return SimpleUploadedFile('documento-sintetico.pdf', signed_pdf_bytes(), content_type='application/pdf')


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
        _, self.template = publish_documents(self.a, self.doctor)
        self.client.force_authenticate(self.doctor)

    def patient(self, clinic, phone):
        return Paciente.objects.create(nombre='A', appat='B', apmat='C', fecha_nacimiento='2000-01-01', genero='F', telefono=phone, email=f'{phone}@example.test', medico=self.doctor, clinic=clinic)

    def post(self, **values):
        return self.client.post(reverse('tenant-consent', args=[self.patient_a.pk]), {**evidence_values(self.template, pdf()), **values}, format='multipart', HTTP_X_CLINIC_ID=str(self.a.pk))

    def test_preserves_original_and_replacement_and_enforces_tenant_download(self):
        response = self.post()
        self.assertEqual(response.status_code, 201, response.data)
        record = ConsentEvidence.objects.get(pk=response.data['id'])
        self.assertTrue(record.signed_document.name.startswith(f'tenants/{self.a.pk}/patients/{self.patient_a.pk}/consents/evidence/'))
        self.assertNotIn('documento-sintetico', record.signed_document.name)
        self.assertEqual(self.post(supersedes_id=record.pk).status_code, 201)
        self.assertEqual(self.post(supersedes_id=record.pk).status_code, 409)
        self.assertEqual(ConsentEvidence.objects.count(), 2)
        url = reverse('consent-evidence-file', args=[self.patient_a.pk, record.pk])
        self.assertEqual(self.client.get(url, HTTP_X_CLINIC_ID=str(self.b.pk)).status_code, 404)
        self.assertEqual(self.client.get(url, HTTP_X_CLINIC_ID=str(self.a.pk)).status_code, 423)
        scan_test_documents()
        response = self.client.get(url, HTTP_X_CLINIC_ID=str(self.a.pk))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b''.join(response.streaming_content).startswith(b'%PDF-'))
        self.assertIn('no-store', response['Cache-Control'])
        self.assertTrue(AuditEvent.objects.filter(clinic=self.a, action='CONSENT_EVIDENCE_RECORDED').exists())
        self.member.status = 'REVOKED'
        self.member.save(update_fields=['status'])
        self.assertEqual(self.client.get(url, HTTP_X_CLINIC_ID=str(self.a.pk)).status_code, 403)

    def test_rejects_legacy_acceptance_empty_text_and_missing_signature_evidence(self):
        url = reverse('tenant-consent', args=[self.patient_a.pk])
        self.assertEqual(self.client.post(url, {'texto': '', 'archivo_ine': pdf()}, format='multipart', HTTP_X_CLINIC_ID=str(self.a.pk)).status_code, 400)
        payload = evidence_values(self.template, pdf())
        payload.pop('signed_document')
        self.assertEqual(self.client.post(url, payload, format='multipart', HTTP_X_CLINIC_ID=str(self.a.pk)).status_code, 400)
        self.assertEqual(self.post(attested=False).status_code, 400)
        self.assertEqual(self.post(signer_role='REPRESENTATIVE', representative_basis='').status_code, 400)
        self.assertFalse(ConsentEvidence.objects.exists())
        self.assertFalse(Consentimiento.objects.exists())

    def test_cross_clinic_and_forged_patient_denied(self):
        foreign = reverse('tenant-consent', args=[self.patient_b.pk])
        self.assertEqual(self.client.post(foreign, evidence_values(self.template, pdf()), format='multipart', HTTP_X_CLINIC_ID=str(self.a.pk)).status_code, 404)
        self.assertEqual(self.post(paciente_id=self.patient_b.pk).status_code, 400)
        self.assertFalse(ConsentEvidence.objects.exists())

    def test_validation_failure_preserves_historical_file(self):
        existing = Consentimiento.objects.create(paciente=self.patient_a, medico=self.doctor, texto='', archivo_ine=pdf())
        original = existing.archivo_ine.name
        self.assertEqual(self.post(signer_name='x'*301).status_code, 400)
        existing.refresh_from_db()
        self.assertEqual(existing.archivo_ine.name, original)
        self.assertTrue(default_storage.exists(original))
        data = self.client.get(reverse('tenant-consent', args=[self.patient_a.pk]), HTTP_X_CLINIC_ID=str(self.a.pk)).data
        self.assertIsNotNone(data['legacy'])
        self.assertEqual(data['records'], [])

    def test_revocation_preserves_document_and_tampered_file_is_not_delivered(self):
        result = self.post()
        record = ConsentEvidence.objects.get(pk=result.data['id'])
        url = reverse('consent-evidence-revoke', args=[self.patient_a.pk, record.pk])
        self.assertEqual(self.client.post(url, {'reason': 'Solicitud sintética del titular'}, HTTP_X_CLINIC_ID=str(self.a.pk)).status_code, 201)
        self.assertTrue(default_storage.exists(record.signed_document.name))
        with default_storage.open(record.signed_document.name, 'wb') as file:
            file.write(b'altered synthetic data')
        self.assertEqual(self.client.get(reverse('consent-evidence-file', args=[self.patient_a.pk, record.pk]), HTTP_X_CLINIC_ID=str(self.a.pk)).status_code, 409)

    @patch('api.tenant_patients.AuditEvent.objects.create', side_effect=RuntimeError('synthetic audit failure'))
    def test_failed_audit_rolls_back_and_removes_new_upload(self, _audit):
        self.client.raise_request_exception = False
        self.assertEqual(self.post().status_code, 500)
        self.assertFalse(ConsentEvidence.objects.exists())
        prefix = f'tenants/{self.a.pk}/patients/{self.patient_a.pk}/consents/evidence'
        self.assertEqual(default_storage.listdir(prefix)[1], [])


@skipUnlessDBFeature('has_select_for_update')
class TenantConsentConcurrencyTests(TransactionTestCase):
    def test_concurrent_replacement_preserves_one_successor(self):
        with TemporaryDirectory() as media, override_settings(MEDIA_ROOT=media):
            doctor = User.objects.create_user('tenant-consent-concurrent')
            clinic = Clinic.objects.create(name='A', slug='consent-concurrent', status='ACTIVE')
            ClinicMembership.objects.create(user=doctor, clinic=clinic, role='DOCTOR', status='ACTIVE')
            patient = Paciente.objects.create(nombre='A', appat='B', apmat='C', fecha_nacimiento='2000-01-01', genero='F', telefono='1234567890', email='consent@example.test', medico=doctor, clinic=clinic)
            _, template = publish_documents(clinic, doctor)
            client = APIClient()
            client.force_authenticate(doctor)
            url = reverse('tenant-consent', args=[patient.pk])
            original = client.post(url, evidence_values(template, pdf()), format='multipart', HTTP_X_CLINIC_ID=str(clinic.pk)).data['id']
            barrier = threading.Barrier(2)

            def accept(_):
                close_old_connections()
                try:
                    client = APIClient()
                    client.force_authenticate(doctor)
                    barrier.wait(timeout=10)
                    return client.post(url, {**evidence_values(template, pdf()), 'supersedes_id': original}, format='multipart', HTTP_X_CLINIC_ID=str(clinic.pk)).status_code
                finally:
                    close_old_connections()

            with ThreadPoolExecutor(max_workers=2) as executor:
                statuses = list(executor.map(accept, (0, 1)))
            self.assertCountEqual(statuses, [201, 409])
            self.assertEqual(ConsentEvidence.objects.filter(patient=patient).count(), 2)


class PrivacyPublisherIdentityTests(APITestCase):
    def test_missing_publisher_name_can_be_corrected_before_retry(self):
        from api.privacy import NOTICE_FIELDS
        from Pacientes.models import PrivacyNotice
        user = User.objects.create_user('publisher-no-name')
        clinic = Clinic.objects.create(name='Synthetic privacy clinic', slug='publisher-name-check', status='ACTIVE')
        ClinicMembership.objects.create(user=user, clinic=clinic, role='CLINIC_ADMIN', status='ACTIVE')
        self.client.force_authenticate(user)
        body = {key: ('privacy@example.test' if key == 'privacy_email' else 'Contenido sintético de prueba') for key in NOTICE_FIELDS}
        body['review_confirmed'] = True
        url = reverse('publish-privacy-notice')
        response = self.client.post(url, body, format='json', HTTP_X_CLINIC_ID=str(clinic.pk))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['code'], 'profile_name_required')
        self.assertFalse(PrivacyNotice.objects.filter(clinic=clinic).exists())
        user.first_name, user.last_name = 'Persona', 'Sintética'
        user.save(update_fields=['first_name', 'last_name'])
        response = self.client.post(url, body, format='json', HTTP_X_CLINIC_ID=str(clinic.pk))
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(PrivacyNotice.objects.get(clinic=clinic).approved_name, 'Persona Sintética')

import uuid
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from DiagnosticosIA.models import AIAnalysisRun
from Pacientes.models import Consulta, ImagenesClinicas, Paciente
from Usuarios.models import AuditEvent, Clinic, ClinicMembership


@override_settings(FEATURE_AI_ENABLED=True)
class TenantImageTests(APITestCase):
    def setUp(self):
        media = self.enterContext(TemporaryDirectory())
        self.enterContext(override_settings(MEDIA_ROOT=media))
        self.doctor = User.objects.create_user('tenant-image-doctor')
        self.a = Clinic.objects.create(name='A', slug='image-clinic-a', status='ACTIVE', ai_enabled=True)
        self.b = Clinic.objects.create(name='B', slug='image-clinic-b', status='ACTIVE', ai_enabled=True)
        self.membership = ClinicMembership.objects.create(user=self.doctor, clinic=self.a, role='DOCTOR', status='ACTIVE')
        ClinicMembership.objects.create(user=self.doctor, clinic=self.b, role='DOCTOR', status='ACTIVE')
        self.patient_a = self.patient(self.a, '1111111111')
        self.patient_b = self.patient(self.b, '2222222222')
        self.consultation_a = Consulta.objects.create(paciente=self.patient_a, medico=self.doctor, fecha_consulta=timezone.now(), motivo_consulta='A')
        self.consultation_b = Consulta.objects.create(paciente=self.patient_b, medico=self.doctor, fecha_consulta=timezone.now(), motivo_consulta='B')
        self.client.force_authenticate(self.doctor)

    def patient(self, clinic, phone):
        return Paciente.objects.create(nombre='A', appat='B', apmat='C', fecha_nacimiento='2000-01-01', genero='F', telefono=phone, email=f'{phone}@example.test', medico=self.doctor, clinic=clinic)

    @staticmethod
    def image_file():
        return SimpleUploadedFile('nombre-sensible.gif', b'GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00ccc,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;', content_type='image/gif')

    def upload(self, patient, consultation, clinic):
        return self.client.post(reverse('tenant-clinical-images', args=[patient.pk]),
            {'consulta_id': consultation.pk, 'tipo_imagen': 'RX', 'descripcion': 'control', 'imagen': self.image_file()},
            format='multipart', HTTP_X_CLINIC_ID=str(clinic.pk))

    def test_upload_and_download_are_clinic_scoped(self):
        response = self.upload(self.patient_a, self.consultation_a, self.a)
        self.assertEqual(response.status_code, 201, response.data)
        image = ImagenesClinicas.objects.get(pk=response.data['id'])
        self.assertTrue(image.imagen.name.startswith(f'tenants/{self.a.pk}/patients/{self.patient_a.pk}/images/'))
        self.assertNotIn('nombre-sensible', image.imagen.name)
        url = reverse('tenant-clinical-image-file', args=[image.pk, 'original'])
        self.assertEqual(self.client.get(url, HTTP_X_CLINIC_ID=str(self.b.pk)).status_code, 404)
        self.assertEqual(self.client.get(reverse('api-clinical-image-file', args=[image.pk])).status_code, 404)
        downloaded = self.client.get(url, HTTP_X_CLINIC_ID=str(self.a.pk))
        self.assertEqual(downloaded.status_code, 200)
        self.assertTrue(b''.join(downloaded.streaming_content).startswith(b'GIF87a'))
        self.assertIn('private', downloaded['Cache-Control'])
        self.assertIn('no-store', downloaded['Cache-Control'])
        self.assertTrue(AuditEvent.objects.filter(action='TENANT_CLINICAL_FILE_VIEWED', clinic=self.a, resource_id=str(image.pk)).exists())
        self.membership.status = 'REVOKED'
        self.membership.save(update_fields=['status'])
        self.assertEqual(self.client.get(url, HTTP_X_CLINIC_ID=str(self.a.pk)).status_code, 403)

    def test_cross_clinic_consultation_and_forged_clinic_are_rejected(self):
        response = self.upload(self.patient_a, self.consultation_b, self.a)
        self.assertEqual(response.status_code, 400)
        url = reverse('tenant-clinical-images', args=[self.patient_a.pk])
        response = self.client.post(url, {'consulta_id': self.consultation_a.pk, 'tipo_imagen': 'RX', 'descripcion': 'control',
                                          'clinic_id': str(self.b.pk), 'imagen': self.image_file()}, format='multipart', HTTP_X_CLINIC_ID=str(self.a.pk))
        self.assertEqual(response.status_code, 400)
        self.assertFalse(ImagenesClinicas.objects.exists())

    def test_archive_keeps_file_and_excludes_image_from_diagnostics(self):
        response = self.upload(self.patient_a, self.consultation_a, self.a)
        self.assertEqual(response.status_code, 201)
        image = ImagenesClinicas.objects.get(pk=response.data['id'])
        name = image.imagen.name
        diagnostics = self.client.get(reverse('tenant-diagnostics'), HTTP_X_CLINIC_ID=str(self.a.pk))
        self.assertEqual(diagnostics.data['statistics']['total'], 1)
        detail = reverse('tenant-clinical-image-detail', args=[image.pk])
        self.assertEqual(self.client.delete(detail, HTTP_X_CLINIC_ID=str(self.b.pk)).status_code, 404)
        self.assertEqual(self.client.delete(detail, HTTP_X_CLINIC_ID=str(self.a.pk)).status_code, 204)
        image.refresh_from_db()
        self.assertFalse(image.is_active)
        self.assertTrue(default_storage.exists(name))
        self.assertEqual(self.client.get(detail, HTTP_X_CLINIC_ID=str(self.a.pk)).status_code, 404)
        diagnostics = self.client.get(reverse('tenant-diagnostics'), HTTP_X_CLINIC_ID=str(self.a.pk))
        self.assertEqual(diagnostics.data['statistics']['total'], 0)
        self.assertTrue(AuditEvent.objects.filter(action='TENANT_CLINICAL_IMAGE_ARCHIVED', clinic=self.a).exists())

    def test_result_requires_matching_successful_run(self):
        image = ImagenesClinicas.objects.create(paciente=self.patient_a, consulta=self.consultation_a, medico=self.doctor,
                                               tipo_imagen='RX', descripcion='test', imagen=self.image_file())
        image.resultados.save('result.png', ContentFile(b'synthetic result'), save=True)
        url = reverse('tenant-clinical-image-file', args=[image.pk, 'result'])
        inconsistent = AIAnalysisRun.objects.create(image=image, clinic=self.b, image_reference=image.pk, requested_by=self.doctor,
                                                    started_at=timezone.now(), status='SUCCEEDED', model_name='test', model_version='a'*64,
                                                    input_hash='b'*64, result_name=image.resultados.name, request_id=uuid.uuid4())
        self.assertEqual(self.client.get(url, HTTP_X_CLINIC_ID=str(self.a.pk)).status_code, 404)
        AIAnalysisRun.objects.create(image=image, clinic=self.a, image_reference=image.pk, requested_by=self.doctor,
                                     started_at=timezone.now(), status='SUCCEEDED', model_name='test', model_version='a'*64,
                                     input_hash='b'*64, result_name=image.resultados.name, request_id=uuid.uuid4())
        self.assertEqual(self.client.get(url, HTTP_X_CLINIC_ID=str(self.a.pk)).status_code, 404)
        inconsistent.clinic = self.a
        inconsistent.save(update_fields=['clinic'])
        response = self.client.get(url, HTTP_X_CLINIC_ID=str(self.a.pk))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b''.join(response.streaming_content), b'synthetic result')

    @patch('api.tenant_patients.AuditEvent.objects.create', side_effect=RuntimeError('synthetic audit failure'))
    def test_upload_audit_failure_removes_new_file(self, _audit):
        self.client.raise_request_exception = False
        response = self.upload(self.patient_a, self.consultation_a, self.a)
        self.assertEqual(response.status_code, 500)
        self.assertFalse(ImagenesClinicas.objects.exists())
        prefix = f'tenants/{self.a.pk}/patients/{self.patient_a.pk}/images'
        self.assertEqual(default_storage.listdir(prefix)[1], [])

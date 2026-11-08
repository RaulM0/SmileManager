from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APITestCase

from Pacientes.models import EstudioComparativo, Paciente
from Usuarios.models import AuditEvent, Clinic, ClinicMembership


FIELDS = ('antes_oclusal_superior', 'antes_lateral_izquierda', 'antes_frontal', 'antes_lateral_derecha', 'antes_oclusal_inferior')
GIF = b'GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00ccc,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'


class TenantStudyTests(APITestCase):
    def setUp(self):
        media = self.enterContext(TemporaryDirectory())
        self.enterContext(override_settings(MEDIA_ROOT=media))
        self.doctor = User.objects.create_user('tenant-study-doctor')
        self.a = Clinic.objects.create(name='A', slug='study-a', status='ACTIVE')
        self.b = Clinic.objects.create(name='B', slug='study-b', status='ACTIVE')
        self.member = ClinicMembership.objects.create(user=self.doctor, clinic=self.a, role='DOCTOR', status='ACTIVE')
        ClinicMembership.objects.create(user=self.doctor, clinic=self.b, role='DOCTOR', status='ACTIVE')
        self.patient_a = self.patient(self.a, '1111111111')
        self.patient_b = self.patient(self.b, '2222222222')
        self.client.force_authenticate(self.doctor)

    def patient(self, clinic, phone):
        return Paciente.objects.create(nombre='A', appat='B', apmat='C', fecha_nacimiento='2000-01-01', genero='F', telefono=phone, email=f'{phone}@example.test', medico=self.doctor, clinic=clinic)

    @staticmethod
    def image():
        return SimpleUploadedFile('nombre-privado.gif', GIF, content_type='image/gif')

    def payload(self):
        return {'fecha_inicio': '2026-01-01', 'diagnostico': 'sintético', **{field: self.image() for field in FIELDS}}

    def create_study(self):
        return self.client.put(reverse('tenant-comparative-study', args=[self.patient_a.pk]), self.payload(), format='multipart', HTTP_X_CLINIC_ID=str(self.a.pk))

    def test_study_files_and_pdf_are_clinic_scoped(self):
        response = self.create_study()
        self.assertEqual(response.status_code, 200, response.data)
        study = EstudioComparativo.objects.get(paciente=self.patient_a)
        self.assertTrue(study.antes_frontal.name.startswith(f'tenants/{self.a.pk}/patients/{self.patient_a.pk}/studies/before/'))
        self.assertNotIn('nombre-privado', study.antes_frontal.name)
        url = reverse('tenant-study-image', args=[self.patient_a.pk, 'antes_frontal'])
        self.assertEqual(self.client.get(url, HTTP_X_CLINIC_ID=str(self.b.pk)).status_code, 404)
        image = self.client.get(url, HTTP_X_CLINIC_ID=str(self.a.pk))
        self.assertEqual(image.status_code, 200)
        self.assertTrue(b''.join(image.streaming_content).startswith(b'GIF87a'))
        self.assertIn('no-store', image['Cache-Control'])
        pdf = self.client.get(reverse('tenant-study-pdf', args=[self.patient_a.pk]), HTTP_X_CLINIC_ID=str(self.a.pk))
        self.assertEqual(pdf.status_code, 200)
        self.assertTrue(pdf.content.startswith(b'%PDF'))
        self.assertTrue(AuditEvent.objects.filter(clinic=self.a, action='TENANT_STUDY_PDF_VIEWED').exists())

    def test_cross_clinic_and_forged_patient_are_rejected(self):
        foreign = reverse('tenant-comparative-study', args=[self.patient_b.pk])
        self.assertEqual(self.client.get(foreign, HTTP_X_CLINIC_ID=str(self.a.pk)).status_code, 404)
        own = reverse('tenant-comparative-study', args=[self.patient_a.pk])
        payload = {**self.payload(), 'paciente_id': str(self.patient_b.pk)}
        self.assertEqual(self.client.put(own, payload, format='multipart', HTTP_X_CLINIC_ID=str(self.a.pk)).status_code, 400)
        self.assertFalse(EstudioComparativo.objects.exists())

    def test_audit_failure_preserves_previous_files_and_removes_new_files(self):
        self.assertEqual(self.create_study().status_code, 200)
        study = EstudioComparativo.objects.get(paciente=self.patient_a)
        old_name = study.antes_frontal.name
        directory = old_name.rsplit('/', 1)[0]
        before = sorted(default_storage.listdir(directory)[1])
        self.client.raise_request_exception = False
        with patch('api.tenant_patients.AuditEvent.objects.create', side_effect=RuntimeError('synthetic audit failure')):
            response = self.client.put(reverse('tenant-comparative-study', args=[self.patient_a.pk]), {'antes_frontal': self.image()}, format='multipart', HTTP_X_CLINIC_ID=str(self.a.pk))
        self.assertEqual(response.status_code, 500)
        study.refresh_from_db()
        self.assertEqual(study.antes_frontal.name, old_name)
        self.assertTrue(default_storage.exists(old_name))
        self.assertEqual(sorted(default_storage.listdir(directory)[1]), before)

    def test_duplicate_studies_require_reconciliation(self):
        for _ in range(2):
            EstudioComparativo.objects.create(paciente=self.patient_a, medico=self.doctor, fecha_inicio='2026-01-01')
        response = self.client.get(reverse('tenant-comparative-study', args=[self.patient_a.pk]), HTTP_X_CLINIC_ID=str(self.a.pk))
        self.assertEqual(response.status_code, 409)

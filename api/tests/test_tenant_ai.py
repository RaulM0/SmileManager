import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import close_old_connections
from django.test import TestCase, TransactionTestCase, override_settings, skipUnlessDBFeature
from django.urls import reverse
from rest_framework.test import APIClient

from DiagnosticosIA.models import AIAnalysisRun
from DiagnosticosIA.runs import audit as write_audit
from Pacientes.models import ImagenesClinicas, Paciente
from Usuarios.models import AuditEvent, Clinic, ClinicMembership


def detached_analyzer(image, *, expected_hash):
    return ([{'clase': 'synthetic', 'confianza': 0.9, 'coordenadas': [0, 0, 1, 1]}], 'result.png', b'synthetic-result')


class TenantAITests(TestCase):
    def setUp(self):
        cache.clear()
        self.media = TemporaryDirectory()
        self.addCleanup(self.media.cleanup)
        self.enterContext(override_settings(MEDIA_ROOT=self.media.name))
        self.doctor = User.objects.create_user('tenant-ai-doctor')
        self.a = Clinic.objects.create(name='A', slug='tenant-ai-a', status='ACTIVE')
        self.b = Clinic.objects.create(name='B', slug='tenant-ai-b', status='ACTIVE')
        self.member = ClinicMembership.objects.create(user=self.doctor, clinic=self.a, role='DOCTOR', status='ACTIVE')
        ClinicMembership.objects.create(user=self.doctor, clinic=self.b, role='DOCTOR', status='ACTIVE')
        self.image_a = self.make_image(self.a, '1111111111')
        self.image_b = self.make_image(self.b, '2222222222')
        self.client = APIClient()
        self.client.force_authenticate(self.doctor)

    def make_image(self, clinic, phone):
        patient = Paciente.objects.create(nombre='A', appat='B', apmat='C', fecha_nacimiento='2000-01-01', genero='F', telefono=phone, email=f'{phone}@example.test', medico=self.doctor, clinic=clinic)
        return ImagenesClinicas.objects.create(paciente=patient, medico=self.doctor, tipo_imagen='RX', imagen=SimpleUploadedFile('synthetic.png', b'synthetic-source'))

    def analyze(self, image, clinic, key=None):
        headers = {'HTTP_X_CLINIC_ID': str(clinic.pk)}
        if key:
            headers['HTTP_IDEMPOTENCY_KEY'] = str(key)
        return self.client.post(reverse('tenant-analyze-image', args=[image.pk]), {'force': bool(key)}, format='json', **headers)

    @patch('DiagnosticosIA.tenant_runs.model_version', return_value='a'*64)
    @patch('api.tenant_ai.analyze_clinical_image_detached', side_effect=detached_analyzer)
    def test_same_key_in_different_clinics_is_independent(self, analyzer, _version):
        key = uuid.uuid4()
        a = self.analyze(self.image_a, self.a, key)
        b = self.analyze(self.image_b, self.b, key)
        self.assertEqual((a.status_code, b.status_code), (200, 200))
        self.assertNotEqual(a.data['run_id'], b.data['run_id'])
        self.assertEqual(self.analyze(self.image_a, self.a, key).data['run_id'], a.data['run_id'])
        self.assertEqual(analyzer.call_count, 2)
        run = AIAnalysisRun.objects.get(pk=a.data['run_id'])
        self.assertEqual(run.clinic_id, self.a.pk)
        self.assertTrue(run.result_name.startswith(f'tenants/{self.a.pk}/patients/{self.image_a.paciente_id}/ai-results/'))
        self.assertTrue(AuditEvent.objects.filter(clinic=self.a, action='AI_ANALYSIS_SUCCEEDED', resource_id=str(run.pk)).exists())
        foreign = reverse('tenant-analysis-run-file', args=[self.image_b.pk, b.data['run_id']])
        self.assertEqual(self.client.get(foreign, HTTP_X_CLINIC_ID=str(self.a.pk)).status_code, 404)
        response = self.client.get(foreign, HTTP_X_CLINIC_ID=str(self.b.pk))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b''.join(response.streaming_content), b'synthetic-result')

    def test_forged_body_clinic_is_rejected_before_inference(self):
        response = self.client.post(reverse('tenant-analyze-image', args=[self.image_a.pk]),
                                    {'force': False, 'clinic_id': str(self.b.pk)}, format='json',
                                    HTTP_X_CLINIC_ID=str(self.a.pk))
        self.assertEqual(response.status_code, 400)
        self.assertFalse(AIAnalysisRun.objects.exists())

    @patch('DiagnosticosIA.tenant_runs.model_version', return_value='a'*64)
    def test_revocation_during_inference_prevents_publication(self, _version):
        def revoke(image, *, expected_hash):
            self.member.status = 'REVOKED'
            self.member.save(update_fields=['status'])
            return detached_analyzer(image, expected_hash=expected_hash)
        with patch('api.tenant_ai.analyze_clinical_image_detached', side_effect=revoke):
            response = self.analyze(self.image_a, self.a)
        self.assertEqual(response.status_code, 403)
        run = AIAnalysisRun.objects.get(image=self.image_a)
        self.assertEqual((run.status, run.failure_category), ('FAILED', 'authorization_revoked'))
        self.image_a.refresh_from_db()
        self.assertFalse(self.image_a.resultados)
        self.assertFalse(run.result_name)

    @patch('DiagnosticosIA.tenant_runs.model_version', return_value='a'*64)
    def test_clinic_suspension_during_inference_prevents_publication(self, _version):
        def suspend(image, *, expected_hash):
            self.a.status = 'SUSPENDED'
            self.a.save(update_fields=['status'])
            return detached_analyzer(image, expected_hash=expected_hash)
        with patch('api.tenant_ai.analyze_clinical_image_detached', side_effect=suspend):
            response = self.analyze(self.image_a, self.a)
        self.assertEqual(response.status_code, 403)
        run = AIAnalysisRun.objects.get(image=self.image_a)
        self.assertEqual((run.status, run.failure_category), ('FAILED', 'authorization_revoked'))
        self.image_a.refresh_from_db()
        self.assertFalse(self.image_a.resultados)

    @patch('DiagnosticosIA.tenant_runs.model_version', return_value='a'*64)
    def test_recovered_run_is_not_overwritten_by_late_inference(self, _version):
        def recover(image, *, expected_hash):
            AIAnalysisRun.objects.filter(image=image, status='RUNNING').update(status='FAILED', failure_category='process_interrupted')
            return detached_analyzer(image, expected_hash=expected_hash)
        with patch('api.tenant_ai.analyze_clinical_image_detached', side_effect=recover):
            response = self.analyze(self.image_a, self.a)
        self.assertEqual(response.status_code, 409)
        run = AIAnalysisRun.objects.get(image=self.image_a)
        self.assertEqual((run.status, run.failure_category), ('FAILED', 'process_interrupted'))
        self.image_a.refresh_from_db()
        self.assertFalse(self.image_a.resultados)

    @patch('DiagnosticosIA.tenant_runs.model_version', return_value='a'*64)
    @patch('api.tenant_ai.analyze_clinical_image_detached', side_effect=detached_analyzer)
    def test_audit_failure_rolls_back_publication_and_removes_file(self, _analyzer, _version):
        def fail_success(user, request_id, action, run, outcome='success'):
            if action == 'AI_ANALYSIS_SUCCEEDED':
                raise RuntimeError('synthetic audit failure')
            return write_audit(user, request_id, action, run, outcome)
        with patch('DiagnosticosIA.tenant_runs.audit', side_effect=fail_success):
            response = self.analyze(self.image_a, self.a)
        self.assertEqual(response.status_code, 500)
        run = AIAnalysisRun.objects.get(image=self.image_a)
        self.assertEqual(run.status, 'FAILED')
        self.image_a.refresh_from_db()
        self.assertFalse(self.image_a.resultados)
        folder = f'tenants/{self.a.pk}/patients/{self.image_a.paciente_id}/ai-results'
        self.assertEqual(default_storage.listdir(folder)[1], [])


@skipUnlessDBFeature('has_select_for_update')
class TenantAIConcurrencyTests(TransactionTestCase):
    def test_two_requests_share_one_running_analysis(self):
        cache.clear()
        with TemporaryDirectory() as media, override_settings(MEDIA_ROOT=media):
            doctor = User.objects.create_user('tenant-ai-concurrent')
            clinic = Clinic.objects.create(name='A', slug='tenant-ai-concurrent', status='ACTIVE')
            ClinicMembership.objects.create(user=doctor, clinic=clinic, role='DOCTOR', status='ACTIVE')
            patient = Paciente.objects.create(nombre='A', appat='B', apmat='C', fecha_nacimiento='2000-01-01', genero='F', telefono='1234567890', email='concurrent@example.test', medico=doctor, clinic=clinic)
            image = ImagenesClinicas.objects.create(paciente=patient, medico=doctor, tipo_imagen='RX', imagen=SimpleUploadedFile('synthetic.png', b'synthetic-source'))
            entered, release = threading.Event(), threading.Event()

            def analyzer(image, *, expected_hash):
                entered.set()
                if not release.wait(15):
                    raise RuntimeError('Test synchronization timed out')
                return detached_analyzer(image, expected_hash=expected_hash)

            def request_analysis():
                close_old_connections()
                try:
                    client = APIClient()
                    client.force_authenticate(doctor)
                    response = client.post(reverse('tenant-analyze-image', args=[image.pk]), {}, format='json', HTTP_X_CLINIC_ID=str(clinic.pk))
                    return response.status_code, response.data
                finally:
                    close_old_connections()

            with patch('DiagnosticosIA.tenant_runs.model_version', return_value='a'*64), patch('api.tenant_ai.analyze_clinical_image_detached', side_effect=analyzer), ThreadPoolExecutor(max_workers=2) as executor:
                first = executor.submit(request_analysis)
                try:
                    self.assertTrue(entered.wait(15))
                    second = executor.submit(request_analysis)
                    second_status, second_data = second.result(timeout=15)
                finally:
                    release.set()
                first_status, first_data = first.result(timeout=15)
            self.assertEqual((first_status, second_status), (200, 202))
            self.assertEqual(first_data['run_id'], second_data['run_id'])
            self.assertEqual(AIAnalysisRun.objects.filter(image=image).count(), 1)

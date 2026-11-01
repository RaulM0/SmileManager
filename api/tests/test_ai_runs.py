from unittest.mock import patch
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from DiagnosticosIA.models import AIAnalysisRun
from Pacientes.models import ImagenesClinicas, Paciente
from Usuarios.models import AuditEvent


class AIAnalysisRunTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user('ai-owner')
        self.other = User.objects.create_user('ai-other')
        patient = Paciente.objects.create(nombre='A', appat='B', apmat='C', fecha_nacimiento='1990-01-01', genero='F', telefono='1234567890', email='a@example.test', medico=self.owner)
        self.image = ImagenesClinicas.objects.create(paciente=patient, medico=self.owner, tipo_imagen='RX', imagen=SimpleUploadedFile('original.bin', b'synthetic input'))
        self.client = APIClient()
        self.client.force_authenticate(self.owner)
        self.url = reverse('api-clinical-image-analyze', args=[self.image.pk])

    @staticmethod
    def fake_analyzer(image, expected_hash):
        image.resultados.save('result.jpg', ContentFile(b'synthetic result'), save=True)
        return [{'clase': 'test', 'confianza': 0.9, 'coordenadas': [1, 2, 3, 4]}]

    @patch('DiagnosticosIA.runs.model_version', return_value='a' * 64)
    @patch('api.views.analyze_clinical_image', side_effect=fake_analyzer.__func__)
    def test_normal_retry_reuse_and_explicit_reanalysis(self, analyzer, version):
        first = self.client.post(self.url, {}, format='json')
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.data['disposition'], 'created')
        retry = self.client.post(self.url, {}, format='json')
        self.assertEqual(retry.data['run_id'], first.data['run_id'])
        self.assertEqual(retry.data['disposition'], 'reused')
        key = '11111111-1111-4111-8111-111111111111'
        force = self.client.post(self.url, {'force': True}, format='json', HTTP_IDEMPOTENCY_KEY=key)
        self.assertEqual(force.status_code, 200)
        self.assertNotEqual(force.data['run_id'], first.data['run_id'])
        repeat = self.client.post(self.url, {'force': True}, format='json', HTTP_IDEMPOTENCY_KEY=key)
        self.assertEqual(repeat.data['run_id'], force.data['run_id'])
        self.assertEqual(analyzer.call_count, 2)
        self.assertTrue(AuditEvent.objects.filter(action='AI_ANALYSIS_REUSED').exists())
        version.return_value = 'b' * 64
        self.assertEqual(self.client.post(self.url, {'force': True}, format='json', HTTP_IDEMPOTENCY_KEY=key).status_code, 409)
        self.assertEqual(self.client.post(self.url, {}, format='json').data['disposition'], 'created')
        self.assertEqual(analyzer.call_count, 3)
        self.image.refresh_from_db()
        self.image.imagen.save('changed.bin', ContentFile(b'other synthetic input'), save=True)
        self.assertEqual(self.client.post(self.url, {}, format='json').data['disposition'], 'created')
        self.assertEqual(analyzer.call_count, 4)
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get(reverse('api-clinical-image-analysis-runs', args=[self.image.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse('api-analysis-run-file', args=[self.image.pk, first.data['run_id']])).status_code, 404)

    @patch('DiagnosticosIA.runs.model_version', return_value='a' * 64)
    @patch('api.views.analyze_clinical_image', side_effect=RuntimeError('sensitive internal error'))
    def test_failure_records_only_category(self, analyzer, version):
        response = self.client.post(self.url, {}, format='json')
        self.assertEqual(response.status_code, 500)
        run = AIAnalysisRun.objects.get()
        self.assertEqual((run.status, run.failure_category), ('FAILED', 'analysis_error'))
        self.assertNotIn('sensitive', response.data['detail'])
        self.assertTrue(AuditEvent.objects.filter(action='AI_ANALYSIS_FAILED', outcome='failure').exists())

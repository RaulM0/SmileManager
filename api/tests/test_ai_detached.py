import hashlib
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from DiagnosticosIA.services import ClinicalImageChangedError, analyze_clinical_image_detached
from Pacientes.models import ImagenesClinicas, Paciente
from Usuarios.models import Clinic


class DetachedAITests(TestCase):
    def test_inference_does_not_publish_result(self):
        with TemporaryDirectory() as media, override_settings(MEDIA_ROOT=media):
            doctor = User.objects.create_user('detached-doctor')
            clinic = Clinic.objects.create(name='A', slug='detached-clinic', status='ACTIVE')
            patient = Paciente.objects.create(nombre='A', appat='B', apmat='C', fecha_nacimiento='2000-01-01', genero='F', telefono='1234567890', email='detached@example.test', medico=doctor, clinic=clinic)
            image = ImagenesClinicas.objects.create(paciente=patient, medico=doctor, tipo_imagen='RX', imagen=SimpleUploadedFile('source.png', b'synthetic-input'))
            with patch('DiagnosticosIA.services._request', return_value={'model_version': 'a'*64, 'filename': 'result.png', 'result': 'c3ludGhldGljLW91dHB1dA==', 'detections': [{'clase': 'synthetic', 'confianza': 0.9, 'coordenadas': [0, 0, 1, 1]}]}):
                detections, filename, data = analyze_clinical_image_detached(image, expected_hash=hashlib.sha256(b'synthetic-input').hexdigest(), expected_version='a'*64)
                self.assertEqual((filename, data), ('result.png', b'synthetic-output'))
                self.assertEqual(detections[0]['clase'], 'synthetic')
                with self.assertRaises(ClinicalImageChangedError):
                    analyze_clinical_image_detached(image, expected_hash='0'*64)
            image.refresh_from_db()
            self.assertFalse(image.resultados)

    def test_service_failure_and_version_validation(self):
        from DiagnosticosIA.services import AIServiceError, model_version
        with override_settings(SMILEIA_URL='', SMILEIA_TOKEN=''):
            with self.assertRaises(AIServiceError):
                model_version()
        with patch('DiagnosticosIA.services._request', return_value={'model_version': 'invalid'}):
            with self.assertRaises(AIServiceError):
                model_version()


@override_settings(SMILEIA_URL='http://smileia:8001', SMILEIA_TOKEN='synthetic-token')
class SmileIAHTTPTests(TestCase):
    @patch('DiagnosticosIA.services.requests.request')
    def test_transport_authentication_and_model_response(self, request):
        from DiagnosticosIA.services import model_version
        response = request.return_value.__enter__.return_value
        response.status_code = 200
        response.iter_content.return_value = [b'{"model_version":"' + b'a' * 64 + b'"}']
        self.assertEqual(model_version(), 'a' * 64)
        request.assert_called_once_with(
            'GET', 'http://smileia:8001/v1/model', data=None,
            headers={'Authorization': 'Bearer synthetic-token'},
            timeout=(5, 100), stream=True, allow_redirects=False,
        )

    @patch('DiagnosticosIA.services.requests.request')
    def test_transport_rejects_failure_invalid_json_and_oversized_body(self, request):
        from DiagnosticosIA.services import AIServiceError, model_version
        response = request.return_value.__enter__.return_value
        for status, body in [(503, b'{}'), (200, b'invalid'), (200, b'[]')]:
            with self.subTest(status=status, body=body):
                response.status_code = status
                response.iter_content.return_value = [body]
                with self.assertRaises(AIServiceError):
                    model_version()
        response.status_code = 200
        response.iter_content.return_value = [b'x' * (1024 * 1024 + 3)]
        with override_settings(CLINICAL_AI_RESULT_MAX_BYTES=1):
            with self.assertRaises(AIServiceError):
                model_version()

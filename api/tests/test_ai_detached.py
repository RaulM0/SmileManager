import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from DiagnosticosIA.services import ClinicalImageChangedError, analyze_clinical_image_detached
from Pacientes.models import ImagenesClinicas, Paciente
from Usuarios.models import Clinic


class FakeModel:
    names = {0: 'synthetic'}

    def predict(self, source, *, save, project, name):
        output = Path(project) / name
        output.mkdir(parents=True)
        (output / 'result.png').write_bytes(b'synthetic-output')
        box = SimpleNamespace(tolist=lambda: [0, 0, 1, 1])
        return [SimpleNamespace(save_dir=output, boxes=SimpleNamespace(cls=[0], conf=[0.9], xyxy=[box]))]


class DetachedAITests(TestCase):
    def test_inference_does_not_publish_result(self):
        with TemporaryDirectory() as media, override_settings(MEDIA_ROOT=media):
            doctor = User.objects.create_user('detached-doctor')
            clinic = Clinic.objects.create(name='A', slug='detached-clinic', status='ACTIVE')
            patient = Paciente.objects.create(nombre='A', appat='B', apmat='C', fecha_nacimiento='2000-01-01', genero='F', telefono='1234567890', email='detached@example.test', medico=doctor, clinic=clinic)
            image = ImagenesClinicas.objects.create(paciente=patient, medico=doctor, tipo_imagen='RX', imagen=SimpleUploadedFile('source.png', b'synthetic-input'))
            with patch('DiagnosticosIA.services.model', FakeModel()):
                detections, filename, data = analyze_clinical_image_detached(image, expected_hash=hashlib.sha256(b'synthetic-input').hexdigest())
                self.assertEqual((filename, data), ('result.png', b'synthetic-output'))
                self.assertEqual(detections[0]['clase'], 'synthetic')
                with self.assertRaises(ClinicalImageChangedError):
                    analyze_clinical_image_detached(image, expected_hash='0'*64)
            image.refresh_from_db()
            self.assertFalse(image.resultados)

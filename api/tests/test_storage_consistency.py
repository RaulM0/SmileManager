import io
import uuid
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from django.db import transaction
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from rest_framework.test import APIClient

from Pacientes.models import Consulta, EstudioComparativo, ImagenesClinicas, Paciente
from Usuarios.models import AuditEvent, Clinic
from DiagnosticosIA.models import AIAnalysisRun

GIF = b'GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00ccc,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'


class StorageAuditTests(TestCase):
    def test_historical_ai_result_is_not_classified_as_orphan(self):
        with TemporaryDirectory() as root, override_settings(MEDIA_ROOT=root):
            name = default_storage.save('resultados/historical.png', ContentFile(b'synthetic'))
            AIAnalysisRun.objects.create(image_reference=1, requested_at=timezone.now(), started_at=timezone.now(), status=AIAnalysisRun.SUCCEEDED, model_name='test', model_version='a'*64, input_hash='b'*64, request_id=uuid.uuid4(), result_name=name)
            output = io.StringIO()
            call_command('audit_storage_consistency', all_clinics=True, include_orphans=True, stdout=output)
            self.assertIn('orphans=0', output.getvalue())
            self.assertTrue(default_storage.exists(name))

    def test_replacement_failures_keep_old_reference_and_delete_never_removes_storage_first(self):
        with TemporaryDirectory() as root, override_settings(MEDIA_ROOT=root):
            user = User.objects.create_user('replace-test')
            patient = Paciente.objects.create(nombre='A', appat='B', apmat='C', fecha_nacimiento='1990-01-01', genero='F', telefono='1234567890', email='a@example.test', medico=user)
            study = EstudioComparativo.objects.create(paciente=patient, medico=user, fecha_inicio='2026-01-01', antes_frontal=SimpleUploadedFile('old.gif', GIF, content_type='image/gif'))
            image = ImagenesClinicas.objects.create(paciente=patient, medico=user, tipo_imagen='RX', imagen=SimpleUploadedFile('original.gif', GIF, content_type='image/gif'))
            old_name = study.antes_frontal.name
            client = APIClient(); client.force_authenticate(user); client.raise_request_exception = False
            url = reverse('api-comparative-study', args=[patient.pk])
            with patch('django.core.files.storage.FileSystemStorage._save', side_effect=OSError('storage failure')):
                with transaction.atomic():
                    self.assertEqual(client.put(url, {'antes_frontal': SimpleUploadedFile('new.gif', GIF, content_type='image/gif')}, format='multipart').status_code, 500)
            study.refresh_from_db()
            self.assertEqual(study.antes_frontal.name, old_name)
            self.assertTrue(default_storage.exists(old_name))
            with patch('django.db.models.query.QuerySet._update', side_effect=RuntimeError('DB failure')):
                with transaction.atomic():
                    self.assertEqual(client.put(url, {'antes_frontal': SimpleUploadedFile('new.gif', GIF, content_type='image/gif')}, format='multipart').status_code, 500)
            study.refresh_from_db()
            self.assertEqual(study.antes_frontal.name, old_name)
            self.assertTrue(default_storage.exists(old_name))
            self.assertTrue(any(path.name.startswith('new') for path in Path(root).rglob('*.gif')))
            image_url = reverse('api-clinical-image-detail', args=[image.pk])
            with patch('django.core.files.storage.FileSystemStorage.delete', side_effect=OSError('delete failure')) as deletion:
                self.assertEqual(client.delete(image_url).status_code, 204)
                deletion.assert_not_called()
            self.assertTrue(default_storage.exists(image.imagen.name))
            second = ImagenesClinicas.objects.create(paciente=patient, medico=user, tipo_imagen='RX', imagen=SimpleUploadedFile('second.gif', GIF, content_type='image/gif'))
            with patch.object(ImagenesClinicas, 'delete', side_effect=RuntimeError('DB failure')), patch('django.core.files.storage.FileSystemStorage.delete') as deletion:
                self.assertEqual(client.delete(reverse('api-clinical-image-detail', args=[second.pk])).status_code, 500)
                deletion.assert_not_called()
            self.assertTrue(ImagenesClinicas.objects.filter(pk=second.pk).exists())
            self.assertTrue(default_storage.exists(second.imagen.name))

    def test_upload_storage_failure_and_db_rollback_are_observed(self):
        with TemporaryDirectory() as root, override_settings(MEDIA_ROOT=root):
            user = User.objects.create_user('failure-test')
            patient = Paciente.objects.create(nombre='A', appat='B', apmat='C', fecha_nacimiento='1990-01-01', genero='F', telefono='1234567890', email='a@example.test', medico=user)
            consultation = Consulta.objects.create(paciente=patient, medico=user, fecha_consulta=timezone.now(), motivo_consulta='Synthetic')
            client = APIClient()
            client.force_authenticate(user)
            client.raise_request_exception = False
            url = reverse('api-clinical-images', args=[patient.pk])

            def payload():
                return {'consulta_id': consultation.pk, 'tipo_imagen': 'RX', 'descripcion': 'Synthetic', 'imagen': SimpleUploadedFile('synthetic.gif', GIF, content_type='image/gif')}

            with patch('django.core.files.storage.FileSystemStorage._save', side_effect=OSError('simulated failure')):
                self.assertEqual(client.post(url, payload(), format='multipart').status_code, 500)
            self.assertFalse(ImagenesClinicas.objects.exists())
            self.assertFalse(AuditEvent.objects.filter(action='CLINICAL_IMAGE_UPLOAD').exists())

            with patch('api.audit.AuditEvent.objects.create', side_effect=RuntimeError('simulated rollback')):
                self.assertEqual(client.post(url, payload(), format='multipart').status_code, 500)
            self.assertFalse(ImagenesClinicas.objects.exists())
            self.assertFalse(AuditEvent.objects.filter(action='CLINICAL_IMAGE_UPLOAD').exists())
            self.assertTrue(any(Path(root).rglob('*.gif')), 'El objeto huérfano demuestra que DB no revierte storage.')

    def test_dry_run_finds_missing_and_orphan_without_disclosing_names(self):
        with TemporaryDirectory() as root, override_settings(MEDIA_ROOT=root):
            user = User.objects.create_user('storage-synthetic')
            patient = Paciente.objects.create(nombre='A', appat='B', apmat='C', fecha_nacimiento='1990-01-01', genero='F', telefono='1234567890', email='a@example.test', medico=user)
            image = ImagenesClinicas.objects.create(paciente=patient, medico=user, tipo_imagen='RX', imagen='imagenes_clinicas/missing.png')
            default_storage.save('imagenes_clinicas/orphan.png', ContentFile(b'synthetic'))
            output = io.StringIO()
            call_command('audit_storage_consistency', all_clinics=True, include_orphans=True, stdout=output)
            self.assertIn(f'MISSING category=ImagenesClinicas.imagen id={image.pk}', output.getvalue())
            self.assertIn('orphans=1', output.getvalue())
            self.assertNotIn('orphan.png', output.getvalue())
            self.assertTrue(Path(root, 'imagenes_clinicas/orphan.png').exists())

    def test_incomplete_reference_scan_cannot_claim_orphans(self):
        user = User.objects.create_user('storage-limited')
        patient = Paciente.objects.create(nombre='A', appat='B', apmat='C', fecha_nacimiento='1990-01-01', genero='F', telefono='1234567890', email='a@example.test', medico=user)
        ImagenesClinicas.objects.bulk_create([ImagenesClinicas(paciente=patient, medico=user, tipo_imagen='RX', imagen=f'imagenes_clinicas/{i}.png') for i in range(2)])
        with patch('api.management.commands.audit_storage_consistency.default_storage.exists', return_value=False):
            with self.assertRaises(CommandError):
                call_command('audit_storage_consistency', all_clinics=True, include_orphans=True, max_references=1, stdout=io.StringIO())

    def test_clinic_scope_only_reports_that_clinics_references(self):
        with TemporaryDirectory() as root, override_settings(MEDIA_ROOT=root):
            user = User.objects.create_user('storage-tenant')
            clinics = [Clinic.objects.create(name=name, slug=f'storage-{name.lower()}', status='ACTIVE') for name in ('A', 'B')]
            images = []
            for index, clinic in enumerate(clinics):
                patient = Paciente.objects.create(nombre='A', appat='B', apmat='C', fecha_nacimiento='1990-01-01', genero='F', telefono=f'{index:010}', email=f'{index}@example.test', medico=user, clinic=clinic)
                images.append(ImagenesClinicas.objects.create(paciente=patient, medico=user, tipo_imagen='RX', imagen=f'tenants/{clinic.pk}/patients/{patient.pk}/images/missing.png'))
            output = io.StringIO()
            call_command('audit_storage_consistency', clinic_id=str(clinics[0].pk), include_orphans=True, stdout=output)
            self.assertIn(f'ImagenesClinicas.imagen id={images[0].pk}', output.getvalue())
            self.assertNotIn(f'ImagenesClinicas.imagen id={images[1].pk}', output.getvalue())
            self.assertIn('tenant_prefix_only=true', output.getvalue())

    def test_clinic_orphan_scan_preserves_detached_and_cross_linked_references(self):
        with TemporaryDirectory() as root, override_settings(MEDIA_ROOT=root):
            user = User.objects.create_user('storage-cross-reference')
            a = Clinic.objects.create(name='A', slug='storage-cross-a', status='ACTIVE')
            b = Clinic.objects.create(name='B', slug='storage-cross-b', status='ACTIVE')
            patient = Paciente.objects.create(nombre='A', appat='B', apmat='C', fecha_nacimiento='1990-01-01', genero='F', telefono='1234567890', email='cross@example.test', medico=user, clinic=b)
            shared = default_storage.save(f'tenants/{a.pk}/patients/1/images/shared.png', ContentFile(b'synthetic'))
            detached = default_storage.save(f'tenants/{a.pk}/patients/1/ai-results/detached.png', ContentFile(b'synthetic'))
            ImagenesClinicas.objects.create(paciente=patient, medico=user, tipo_imagen='RX', imagen=shared)
            AIAnalysisRun.objects.create(clinic=a, image=None, image_reference=99, started_at=timezone.now(), status='SUCCEEDED', model_name='test', model_version='a'*64, input_hash='b'*64, result_name=detached, request_id=uuid.uuid4())
            output = io.StringIO()
            call_command('audit_storage_consistency', clinic_id=str(a.pk), include_orphans=True, stdout=output)
            self.assertIn('orphans=0', output.getvalue())
            self.assertNotIn('POTENTIAL_ORPHAN', output.getvalue())

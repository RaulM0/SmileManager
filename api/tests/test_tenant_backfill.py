import hashlib
import json
import threading
import uuid
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import skipUnless

from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import close_old_connections, connection, transaction
from django.test import TestCase, TransactionTestCase
from django.utils import timezone

from DiagnosticosIA.models import AIAnalysisRun
from Pacientes.models import AntescedentesMedicos, ClinicalRevision, ImagenesClinicas, Paciente
from Usuarios.models import AuditEvent, Clinic, ClinicMembership, PlatformAdmin


class TenantBackfillTests(TestCase):
    def setUp(self):
        self.doctor = User.objects.create_user('backfill-doctor')
        self.admin = User.objects.create_user('backfill-admin')
        PlatformAdmin.objects.create(user=self.admin, is_active=True)
        self.clinic = Clinic.objects.create(name='Sintética', slug='backfill-clinic', status='ACTIVE')
        ClinicMembership.objects.create(user=self.doctor, clinic=self.clinic, role='DOCTOR', status='ACTIVE')
        self.patient = Paciente.objects.create(nombre='Sintético', appat='Prueba', apmat='Demo', fecha_nacimiento='2000-01-01', genero='F', telefono='5551111111', email='backfill@example.test', medico=self.doctor)
        history = AntescedentesMedicos.objects.create(paciente=self.patient, medico=self.doctor)
        self.revision = ClinicalRevision.objects.create(patient=self.patient, resource_type='medical_history', resource_id=history.pk, version=1, snapshot={'synthetic': True})
        image = ImagenesClinicas.objects.create(paciente=self.patient, medico=self.doctor, tipo_imagen='RX', imagen='synthetic.png')
        self.run = AIAnalysisRun.objects.create(image=image, image_reference=image.pk, requested_by=self.doctor, started_at=timezone.now(), status='SUCCEEDED', model_name='test', model_version='a'*64, input_hash='b'*64, request_id=uuid.uuid4())

    def command(self, rows, **options):
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'manifest.json'
            contents = json.dumps(rows).encode('utf-8')
            path.write_bytes(contents)
            options.setdefault('expected_sha256', hashlib.sha256(contents).hexdigest())
            output = StringIO()
            call_command('backfill_tenant_assignments', manifest=str(path), stdout=output, **options)
            return output.getvalue()

    def row(self):
        return {'patient_id': self.patient.pk, 'clinic_id': str(self.clinic.pk)}

    def test_default_is_read_only_and_prints_review_digest(self):
        result = self.command([self.row()])
        self.assertIn('dry_run=true', result)
        self.assertIn('writes=0', result)
        self.patient.refresh_from_db()
        self.assertIsNone(self.patient.clinic_id)

    @skipUnless(connection.vendor == 'postgresql', 'requires real PostgreSQL locking')
    def test_apply_is_atomic_audited_and_idempotent(self):
        options = dict(apply=True, maintenance_confirmed=True, backup_confirmed=True, actor_id=self.admin.pk)
        result = self.command([self.row()], **options)
        self.assertIn('patients=1 revisions=1 ai_runs=1', result)
        for item in (self.patient, self.revision, self.run):
            item.refresh_from_db()
            self.assertEqual(item.clinic_id, self.clinic.pk)
        self.assertTrue(AuditEvent.objects.filter(actor=self.admin, clinic=self.clinic, action='TENANT_BACKFILL_BATCH_APPLIED').exists())
        self.assertIn('patients=0 revisions=0 ai_runs=0', self.command([self.row()], **options))

    @skipUnless(connection.vendor == 'postgresql', 'requires real PostgreSQL locking')
    def test_inconsistent_batch_or_unverified_operator_changes_nothing(self):
        options = dict(apply=True, maintenance_confirmed=True, backup_confirmed=True, actor_id=self.admin.pk)
        with self.assertRaises(CommandError):
            self.command([self.row()], **{**options, 'expected_sha256': '0'*64})
        with self.assertRaises(CommandError):
            self.command([self.row()], **{**options, 'actor_id': self.doctor.pk})
        self.revision.resource_id = 999999
        self.revision.save(update_fields=['resource_id'])
        with self.assertRaises(CommandError):
            self.command([self.row()], **options)
        for item in (self.patient, self.revision, self.run):
            item.refresh_from_db()
            self.assertIsNone(item.clinic_id)
        self.assertFalse(AuditEvent.objects.filter(action='TENANT_BACKFILL_BATCH_APPLIED').exists())


@skipUnless(connection.vendor == 'postgresql', 'requires real PostgreSQL locking')
class TenantBackfillConcurrencyTests(TransactionTestCase):
    def test_competing_writer_causes_bounded_failure_without_partial_assignment(self):
        doctor = User.objects.create_user('backfill-race-doctor')
        admin = User.objects.create_user('backfill-race-admin')
        PlatformAdmin.objects.create(user=admin, is_active=True)
        clinic = Clinic.objects.create(name='Sintética', slug='backfill-race', status='ACTIVE')
        ClinicMembership.objects.create(user=doctor, clinic=clinic, role='DOCTOR', status='ACTIVE')
        patient = Paciente.objects.create(nombre='Sintético', appat='Prueba', apmat='Demo', fecha_nacimiento='2000-01-01', genero='F', telefono='5552222222', email='race@example.test', medico=doctor)
        locked, release = threading.Event(), threading.Event()
        failures = []

        def writer():
            close_old_connections()
            try:
                with transaction.atomic():
                    Paciente.objects.filter(pk=patient.pk).update(nombre='Prueba sintética')
                    locked.set()
                    if not release.wait(10):
                        raise RuntimeError('Writer was not released')
            except Exception as exc:
                failures.append(exc)
                locked.set()
            finally:
                close_old_connections()

        thread = threading.Thread(target=writer)
        thread.start()
        try:
            self.assertTrue(locked.wait(10))
            self.assertFalse(failures)
            contents = json.dumps([{'patient_id': patient.pk, 'clinic_id': str(clinic.pk)}]).encode()
            with TemporaryDirectory() as directory:
                manifest = Path(directory) / 'manifest.json'
                manifest.write_bytes(contents)
                with self.assertRaisesMessage(CommandError, 'Could not acquire migration locks'):
                    call_command('backfill_tenant_assignments', manifest=str(manifest), apply=True,
                                 maintenance_confirmed=True, backup_confirmed=True, actor_id=admin.pk,
                                 expected_sha256=hashlib.sha256(contents).hexdigest(), lock_timeout_seconds=1,
                                 stdout=StringIO())
        finally:
            release.set()
            thread.join(10)
        self.assertFalse(thread.is_alive())
        self.assertFalse(failures)
        patient.refresh_from_db()
        self.assertIsNone(patient.clinic_id)
        self.assertFalse(AuditEvent.objects.filter(action='TENANT_BACKFILL_BATCH_APPLIED').exists())

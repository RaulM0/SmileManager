import json
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from Pacientes.models import ClinicalRevision, Paciente
from Usuarios.models import Clinic, ClinicMembership


class AssignmentValidationTests(TestCase):
    def setUp(self):
        self.doctor = User.objects.create_user('doctor-migration')
        self.clinic = Clinic.objects.create(name='A', slug='migration-a', status='ACTIVE')
        ClinicMembership.objects.create(user=self.doctor, clinic=self.clinic, role='DOCTOR', status='ACTIVE')
        self.patient = Paciente.objects.create(nombre='A', appat='B', apmat='C', fecha_nacimiento='2000-01-01', genero='F', telefono='1234567890', email='a@example.com', medico=self.doctor)

    def validate(self, rows):
        with TemporaryDirectory() as directory:
            manifest = Path(directory) / 'assignments.json'
            manifest.write_text(json.dumps(rows), encoding='utf-8')
            output = StringIO()
            call_command('validate_tenant_assignments', manifest=str(manifest), stdout=output)
            return output.getvalue()

    def test_valid_manifest_is_read_only(self):
        result = self.validate([{'patient_id': self.patient.pk, 'clinic_id': str(self.clinic.pk)}])
        self.assertIn('mappings=1 problems=0 writes=0', result)
        self.patient.refresh_from_db()
        self.assertIsNone(self.patient.clinic_id)

    def test_conflicting_revision_blocks_validation(self):
        ClinicalRevision.objects.create(patient=self.patient, resource_type='medical_history', resource_id=9999, version=1, snapshot={})
        with self.assertRaises(CommandError):
            self.validate([{'patient_id': self.patient.pk, 'clinic_id': str(self.clinic.pk)}])
        self.patient.refresh_from_db()
        self.assertIsNone(self.patient.clinic_id)

    def test_duplicate_patient_and_missing_membership_are_rejected(self):
        row = {'patient_id': self.patient.pk, 'clinic_id': str(self.clinic.pk)}
        with self.assertRaises(CommandError):
            self.validate([row, row])
        ClinicMembership.objects.filter(clinic=self.clinic, user=self.doctor).update(status='REVOKED')
        with self.assertRaises(CommandError):
            self.validate([row])

    def test_existing_clinic_contact_conflict_blocks_backfill(self):
        Paciente.objects.create(nombre='B', appat='B', apmat='C', fecha_nacimiento='2000-01-01', genero='F', telefono=self.patient.telefono, email='other@example.test', medico=self.doctor, clinic=self.clinic)
        with self.assertRaises(CommandError):
            self.validate([{'patient_id': self.patient.pk, 'clinic_id': str(self.clinic.pk)}])
        self.patient.refresh_from_db()
        self.assertIsNone(self.patient.clinic_id)

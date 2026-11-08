"""Read-only validation of an explicit patient-to-clinic migration manifest."""
import json
from pathlib import Path
from uuid import UUID

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Exists, F, OuterRef, Q

from DiagnosticosIA.models import AIAnalysisRun
from Pacientes.models import (AntescedentesMedicos, ClinicalRevision, Consulta,
                              Consentimiento, EstudioComparativo, ImagenesClinicas,
                              Odontograma, Paciente)
from Usuarios.models import Clinic, ClinicMembership


class Command(BaseCommand):
    help = 'Validate explicit patient-to-clinic assignments without changing data.'

    def add_arguments(self, parser):
        parser.add_argument('--manifest', required=True, help='JSON array of patient_id and clinic_id mappings')

    def handle(self, *args, **options):
        path = Path(options['manifest'])
        try:
            if path.stat().st_size > 1_000_000:
                raise CommandError('Manifest exceeds the size limit.')
            data = json.loads(path.read_text(encoding='utf-8-sig'))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise CommandError('Cannot read a valid JSON manifest.') from exc
        if not isinstance(data, list) or not data or len(data) > 500:
            raise CommandError('Manifest must be a non-empty array of at most 500 mappings.')
        mappings = []
        seen = set()
        for row in data:
            if not isinstance(row, dict) or set(row) != {'patient_id', 'clinic_id'}:
                raise CommandError('Each mapping must contain only patient_id and clinic_id.')
            patient_id = row['patient_id']
            if isinstance(patient_id, bool) or not isinstance(patient_id, int) or not 1 <= patient_id <= 2**63 - 1 or patient_id in seen:
                raise CommandError('Patient IDs must be unique positive integers.')
            try:
                clinic_id = UUID(str(row['clinic_id']))
            except (ValueError, TypeError, AttributeError) as exc:
                raise CommandError('Invalid clinic UUID.') from exc
            mappings.append((patient_id, clinic_id))
            seen.add(patient_id)

        problems = []
        for position, (patient_id, clinic_id) in enumerate(mappings, 1):
            patient = Paciente.objects.filter(pk=patient_id).only('id', 'clinic_id', 'medico_id', 'telefono', 'email').first()
            clinic_exists = Clinic.objects.filter(pk=clinic_id).exists()
            if patient is None or not clinic_exists:
                problems.append((position, 'missing_patient_or_clinic'))
                continue
            if patient.clinic_id is not None and patient.clinic_id != clinic_id:
                problems.append((position, 'patient_already_assigned_elsewhere'))
            if patient.medico_id and Paciente.objects.filter(clinic_id=clinic_id, medico_id=patient.medico_id).exclude(pk=patient.pk).filter(
                    Q(telefono=patient.telefono) | Q(email=patient.email)).exists():
                problems.append((position, 'contact_conflict_in_clinic'))
            if not patient.medico_id or not ClinicMembership.objects.filter(
                    clinic_id=clinic_id, user_id=patient.medico_id, user__is_active=True,
                    status=ClinicMembership.Status.ACTIVE, role=ClinicMembership.Role.DOCTOR).exists():
                problems.append((position, 'doctor_membership_not_active'))
            for model in (AntescedentesMedicos, Consulta, ImagenesClinicas, Odontograma, EstudioComparativo, Consentimiento):
                if model.objects.filter(paciente_id=patient_id).exclude(medico_id=patient.medico_id).exists():
                    problems.append((position, f'{model._meta.model_name}_doctor_mismatch'))
            if ImagenesClinicas.objects.filter(paciente_id=patient_id, consulta__isnull=False).exclude(
                    Q(consulta__paciente_id=F('paciente_id')) & Q(consulta__medico_id=F('medico_id'))).exists():
                problems.append((position, 'image_consultation_mismatch'))
            if ClinicalRevision.objects.filter(patient_id=patient_id, clinic__isnull=False).exclude(clinic_id=clinic_id).exists():
                problems.append((position, 'revision_clinic_mismatch'))
            revisions = ClinicalRevision.objects.filter(patient_id=patient_id).annotate(
                valid_history=Exists(AntescedentesMedicos.objects.filter(pk=OuterRef('resource_id'), paciente_id=patient_id)),
                valid_odontogram=Exists(Odontograma.objects.filter(pk=OuterRef('resource_id'), paciente_id=patient_id)),
            )
            if revisions.exclude(Q(resource_type='medical_history', valid_history=True) | Q(resource_type='odontogram', valid_odontogram=True)).exists():
                problems.append((position, 'revision_resource_mismatch'))
            runs = AIAnalysisRun.objects.filter(image__paciente_id=patient_id)
            if runs.filter(clinic__isnull=False).exclude(clinic_id=clinic_id).exists():
                problems.append((position, 'analysis_clinic_mismatch'))
            if runs.filter(status=AIAnalysisRun.RUNNING).exists():
                problems.append((position, 'analysis_in_progress'))
        for position, reason in problems:
            self.stdout.write(f'row={position} problem={reason}')
        self.stdout.write(f'mappings={len(mappings)} problems={len(problems)} writes=0')
        if problems:
            raise CommandError('Manifest requires reconciliation; no data was changed.')

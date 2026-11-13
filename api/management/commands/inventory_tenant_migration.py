"""Aggregate-only, read-only inventory; never infer a clinic assignment."""
from django.core.management.base import BaseCommand
from django.db.models import F, Q

from DiagnosticosIA.models import AIAnalysisRun
from Pacientes.models import (AntescedentesMedicos, ClinicalRevision, Consulta,
                              Consentimiento, EstudioComparativo, ImagenesClinicas,
                              Odontograma, Paciente)
from Usuarios.models import AuditEvent


class Command(BaseCommand):
    help = 'Print aggregate migration risks without changing records or assigning clinics.'

    def handle(self, *args, **options):
        counts = {
            'patients_total': Paciente.objects.count(),
            'patients_without_clinic': Paciente.objects.filter(clinic__isnull=True).count(),
            'patients_without_doctor': Paciente.objects.filter(medico__isnull=True).count(),
            'revisions_without_patient': ClinicalRevision.objects.filter(patient__isnull=True).count(),
            'ai_runs_without_image': AIAnalysisRun.objects.filter(image__isnull=True).count(),
            'audit_events_without_clinic_provenance': AuditEvent.objects.filter(clinic__isnull=True).count(),
            'revisions_without_clinic': ClinicalRevision.objects.filter(clinic__isnull=True).count(),
            'ai_runs_without_clinic': AIAnalysisRun.objects.filter(clinic__isnull=True).count(),
            'revision_clinic_mismatch': ClinicalRevision.objects.filter(clinic__isnull=False, patient__clinic__isnull=False).exclude(clinic_id=F('patient__clinic_id')).count(),
            'ai_run_clinic_mismatch': AIAnalysisRun.objects.filter(clinic__isnull=False, image__paciente__clinic__isnull=False).exclude(clinic_id=F('image__paciente__clinic_id')).count(),
            'images_with_inconsistent_consultation': ImagenesClinicas.objects.filter(consulta__isnull=False).exclude(
                Q(consulta__paciente_id=F('paciente_id')) & Q(consulta__medico_id=F('medico_id'))).count(),
        }
        for model in (AntescedentesMedicos, Consulta, ImagenesClinicas, Odontograma, EstudioComparativo, Consentimiento):
            counts[f'{model._meta.model_name}_doctor_mismatch'] = model.objects.exclude(medico_id=F('paciente__medico_id')).count()
            counts[f'{model._meta.model_name}_patient_without_doctor'] = model.objects.filter(paciente__medico__isnull=True).count()
        for key, value in counts.items():
            self.stdout.write(f'{key}={value}')
        self.stdout.write('No clinic assignments were inferred or written.')

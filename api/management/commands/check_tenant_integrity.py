"""Read-only release gate for clinical tenant provenance; no inferred backfill."""
import json

from django.core.management.base import BaseCommand, CommandError
from django.db.models import F, Q

from DiagnosticosIA.models import AIAnalysisRun
from Pacientes.models import (Paciente, AntescedentesMedicos, Consulta, ImagenesClinicas,
                              Odontograma, EstudioComparativo, Consentimiento, ClinicalRevision)


def integrity_counts():
    counts = {
        'patients_without_clinic': Paciente.objects.filter(clinic__isnull=True).count(),
        'patients_without_doctor': Paciente.objects.filter(medico__isnull=True).count(),
        'images_with_inconsistent_consultation': ImagenesClinicas.objects.filter(consulta__isnull=False).exclude(
            Q(consulta__paciente_id=F('paciente_id')) & Q(consulta__medico_id=F('medico_id'))).count(),
        'revisions_without_patient_or_clinic': ClinicalRevision.objects.filter(Q(patient__isnull=True) | Q(clinic__isnull=True)).count(),
        'revision_clinic_mismatch': ClinicalRevision.objects.filter(patient__isnull=False).exclude(clinic_id=F('patient__clinic_id')).count(),
        'ai_runs_without_image_or_clinic': AIAnalysisRun.objects.filter(Q(image__isnull=True) | Q(clinic__isnull=True)).count(),
        'ai_run_clinic_mismatch': AIAnalysisRun.objects.filter(image__isnull=False).exclude(clinic_id=F('image__paciente__clinic_id')).count(),
        'accepted_consents_without_pdf': Consentimiento.objects.filter(fecha_aceptacion__isnull=False).filter(Q(pdf_generado='') | Q(pdf_generado__isnull=True)).count(),
    }
    for model in (AntescedentesMedicos, Consulta, ImagenesClinicas, Odontograma, EstudioComparativo, Consentimiento):
        counts[f'{model._meta.model_name}_doctor_mismatch'] = model.objects.exclude(medico_id=F('paciente__medico_id')).count()
    return counts


class Command(BaseCommand):
    help = 'Verifica invariantes multitenant sin escribir; falla si hay datos pendientes de conciliación.'

    def handle(self, *args, **options):
        counts = integrity_counts()
        self.stdout.write(json.dumps(counts, sort_keys=True))
        if any(counts.values()):
            raise CommandError('Integridad multitenant pendiente. Conciliar datos mediante el procedimiento de migración; no se modificó ningún registro.')
        self.stdout.write(self.style.SUCCESS('Integridad multitenant correcta. No se modificaron datos.'))

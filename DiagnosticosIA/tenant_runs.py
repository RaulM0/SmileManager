"""Tenant inference lifecycle: infer without locks, authorize before publishing."""
import logging

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied

from Pacientes.access import clinic_clinical_queryset
from Usuarios.clinic_context import lock_clinic_capability, require_clinic_capability
from Pacientes.models import ImagenesClinicas, Paciente
from .models import AIAnalysisRun
from .runs import AnalysisClinicConflict, AnalysisKeyConflict, audit, input_digest
from .services import ClinicalImageChangedError, ClinicalImageMissingError, model_version

logger = logging.getLogger(__name__)


class AnalysisInterrupted(Exception):
    pass


def _locked_context(user, clinic_id):
    """Caller holds an atomic transaction; clinic is always locked first."""
    membership = lock_clinic_capability(user, clinic_id, 'clinical.assigned')
    return membership.user


def _locked_image(user, clinic_id, image_id, patient_id):
    patients = clinic_clinical_queryset(user, clinic_id, Paciente).select_for_update(of=('self',))
    patient = get_object_or_404(patients, pk=patient_id)
    images = clinic_clinical_queryset(user, clinic_id, ImagenesClinicas).select_for_update(of=('self',))
    image = get_object_or_404(images, pk=image_id, paciente_id=patient.pk)
    image.paciente = patient
    return image


def execute_tenant_analysis(*, user, clinic_id, image_id, request_id, force, analyzer, idempotency_key=None):
    require_clinic_capability(user, clinic_id, 'clinical.assigned')
    images = clinic_clinical_queryset(user, clinic_id, ImagenesClinicas).select_related('paciente')
    image = get_object_or_404(images, pk=image_id)
    patient_id, original_name = image.paciente_id, image.imagen.name
    if not original_name:
        raise ClinicalImageMissingError
    if AIAnalysisRun.objects.filter(image=image).exclude(clinic_id=clinic_id).exists():
        raise AnalysisClinicConflict
    input_hash = input_digest(image)
    version = model_version()
    candidate = None
    candidate_exists = False
    if not force:
        candidate = AIAnalysisRun.objects.filter(image=image, clinic_id=clinic_id, model_version=version,
                                                 input_hash=input_hash, status=AIAnalysisRun.SUCCEEDED).order_by('-pk').first()
        candidate_exists = bool(candidate and candidate.result_name and image.resultados.name == candidate.result_name
                                and default_storage.exists(candidate.result_name))

    with transaction.atomic():
        account = _locked_context(user, clinic_id)
        image = _locked_image(account, clinic_id, image_id, patient_id)
        if image.imagen.name != original_name:
            raise ClinicalImageChangedError
        if AIAnalysisRun.objects.filter(image=image).exclude(clinic_id=clinic_id).exists():
            raise AnalysisClinicConflict
        if idempotency_key:
            previous = AIAnalysisRun.objects.filter(image=image, clinic_id=clinic_id, requested_by=account, idempotency_key=idempotency_key).first()
            if previous:
                if previous.input_hash != input_hash or previous.model_version != version or previous.explicit_reanalysis != force:
                    raise AnalysisKeyConflict
                audit(account, request_id, 'AI_ANALYSIS_REUSED' if previous.status != AIAnalysisRun.FAILED else 'AI_ANALYSIS_RETRY_FAILED', previous,
                      'failure' if previous.status == AIAnalysisRun.FAILED else 'success')
                return previous, 'running' if previous.status == AIAnalysisRun.RUNNING else 'reused'
        active = AIAnalysisRun.objects.filter(image=image, status=AIAnalysisRun.RUNNING).first()
        if active:
            audit(account, request_id, 'AI_ANALYSIS_IN_PROGRESS', active)
            return active, 'running'
        if candidate_exists and candidate and image.resultados.name == candidate.result_name:
            audit(account, request_id, 'AI_ANALYSIS_REUSED', candidate)
            return candidate, 'reused'
        run = AIAnalysisRun.objects.create(image=image, clinic_id=clinic_id, image_reference=image.pk,
                                           requested_by=account, started_at=timezone.now(), status=AIAnalysisRun.RUNNING,
                                           model_name='YOLO', model_version=version, input_hash=input_hash,
                                           request_id=request_id, explicit_reanalysis=force, idempotency_key=idempotency_key)
        audit(account, request_id, 'AI_REANALYSIS_REQUESTED' if force else 'AI_ANALYSIS_REQUESTED', run)

    saved_name = None
    try:
        detections, filename, result_bytes = analyzer(image, expected_hash=input_hash)
        if not isinstance(result_bytes, bytes) or not result_bytes:
            raise ValueError('El análisis no produjo un archivo válido.')
        with transaction.atomic():
            account = _locked_context(user, clinic_id)
            image = _locked_image(account, clinic_id, image_id, patient_id)
            run = AIAnalysisRun.objects.select_for_update().get(pk=run.pk, image=image, clinic_id=clinic_id)
            if run.status != AIAnalysisRun.RUNNING:
                raise AnalysisInterrupted
            if image.imagen.name != original_name:
                raise ClinicalImageChangedError
            if AIAnalysisRun.objects.filter(image=image).exclude(clinic_id=clinic_id).exists():
                raise AnalysisClinicConflict
            image.resultados.save(filename, ContentFile(result_bytes), save=False)
            saved_name = image.resultados.name
            image.save(update_fields=['resultados'])
            run.status = AIAnalysisRun.SUCCEEDED
            run.completed_at = timezone.now()
            run.result_name = saved_name
            run.detections = detections
            run.save(update_fields=['status', 'completed_at', 'result_name', 'detections'])
            audit(account, request_id, 'AI_ANALYSIS_SUCCEEDED', run)
        return run, 'created'
    except Exception as exc:
        if saved_name:
            try:
                default_storage.delete(saved_name)
            except Exception:
                logger.exception('No fue posible limpiar el resultado IA después de un error de transacción.')
        with transaction.atomic():
            failed = AIAnalysisRun.objects.select_for_update().filter(pk=run.pk, status=AIAnalysisRun.RUNNING).first()
            if failed:
                failed.status = AIAnalysisRun.FAILED
                failed.completed_at = timezone.now()
                failed.failure_category = ('authorization_revoked' if isinstance(exc, PermissionDenied) else
                                           'source_missing' if isinstance(exc, ClinicalImageMissingError) else
                                           'input_changed' if isinstance(exc, ClinicalImageChangedError) else 'analysis_error')
                failed.save(update_fields=['status', 'completed_at', 'failure_category'])
                audit(user, request_id, 'AI_ANALYSIS_FAILED', failed, 'failure')
        raise

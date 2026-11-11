"""Ejecuciones síncronas; no mantiene locks durante inferencia ni storage."""
import hashlib
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone

from Pacientes.access import clinic_clinical_queryset, scoped
from Pacientes.models import ImagenesClinicas
from Usuarios.models import AuditEvent
from .models import AIAnalysisRun
from .services import ClinicalImageMissingError, ClinicalImageChangedError, model_version

class AnalysisKeyConflict(Exception):
    pass


class AnalysisClinicConflict(Exception):
    pass


def input_digest(image):
    digest = hashlib.sha256()
    try:
        with image.imagen.open('rb') as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b''):
                digest.update(chunk)
    except FileNotFoundError as exc:
        raise ClinicalImageMissingError from exc
    return digest.hexdigest()


def audit(user, request_id, action, run, outcome='success'):
    AuditEvent.objects.create(actor=user, clinic_id=run.clinic_id, request_id=request_id, action=action, outcome=outcome, resource_type='ai_run', resource_id=str(run.pk))


def execute(*, user, image_id, request_id, force, analyzer, idempotency_key=None, clinic_id=None):
    def authorized_images():
        return clinic_clinical_queryset(user, clinic_id, ImagenesClinicas) if clinic_id is not None else scoped(user, ImagenesClinicas)

    image = get_object_or_404(authorized_images(), pk=image_id)
    if AIAnalysisRun.objects.filter(image=image).exclude(clinic_id=image.paciente.clinic_id).exists():
        raise AnalysisClinicConflict
    if not image.imagen:
        raise ClinicalImageMissingError
    input_hash = input_digest(image)
    version = model_version()
    candidate = None
    candidate_exists = False
    if not force:
        candidate = AIAnalysisRun.objects.filter(image=image, model_version=version, input_hash=input_hash, status=AIAnalysisRun.SUCCEEDED).order_by('-pk').first()
        candidate_exists = bool(candidate and candidate.result_name and image.resultados.name == candidate.result_name and image.resultados.storage.exists(candidate.result_name))
    with transaction.atomic():
        image = get_object_or_404(authorized_images().select_for_update(of=('self',)), pk=image_id)
        if AIAnalysisRun.objects.filter(image=image).exclude(clinic_id=image.paciente.clinic_id).exists():
            raise AnalysisClinicConflict
        if idempotency_key:
            previous = AIAnalysisRun.objects.filter(image=image, requested_by=user, idempotency_key=idempotency_key).first()
            if previous:
                if previous.input_hash != input_hash or previous.model_version != version or previous.explicit_reanalysis != force:
                    raise AnalysisKeyConflict
                audit(user, request_id, 'AI_ANALYSIS_REUSED' if previous.status != AIAnalysisRun.FAILED else 'AI_ANALYSIS_RETRY_FAILED', previous, 'failure' if previous.status == AIAnalysisRun.FAILED else 'success')
                return previous, 'running' if previous.status == AIAnalysisRun.RUNNING else 'reused'
        active = AIAnalysisRun.objects.filter(image=image, status=AIAnalysisRun.RUNNING).first()
        if active:
            audit(user, request_id, 'AI_ANALYSIS_IN_PROGRESS', active)
            return active, 'running'
        if not force and candidate_exists:
            if candidate and image.resultados.name == candidate.result_name:
                audit(user, request_id, 'AI_ANALYSIS_REUSED', candidate)
                return candidate, 'reused'
        run = AIAnalysisRun.objects.create(image=image, clinic_id=image.paciente.clinic_id, image_reference=image.pk, requested_by=user, started_at=timezone.now(), status=AIAnalysisRun.RUNNING, model_name='YOLO', model_version=version, input_hash=input_hash, request_id=request_id, explicit_reanalysis=force, idempotency_key=idempotency_key)
        audit(user, request_id, 'AI_REANALYSIS_REQUESTED' if force else 'AI_ANALYSIS_REQUESTED', run)
    try:
        detections = analyzer(image, expected_hash=input_hash)
        image.refresh_from_db()
        with transaction.atomic():
            run.status = AIAnalysisRun.SUCCEEDED
            run.completed_at = timezone.now()
            run.result_name = image.resultados.name or ''
            run.detections = detections
            run.save(update_fields=['status', 'completed_at', 'result_name', 'detections'])
            audit(user, request_id, 'AI_ANALYSIS_SUCCEEDED', run)
        return run, 'created'
    except Exception as exc:
        with transaction.atomic():
            run.status = AIAnalysisRun.FAILED
            run.completed_at = timezone.now()
            run.failure_category = 'source_missing' if isinstance(exc, ClinicalImageMissingError) else 'input_changed' if isinstance(exc, ClinicalImageChangedError) else 'analysis_error'
            run.save(update_fields=['status', 'completed_at', 'failure_category'])
            audit(user, request_id, 'AI_ANALYSIS_FAILED', run, 'failure')
        raise

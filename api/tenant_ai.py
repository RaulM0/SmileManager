"""Tenant AI endpoints with per-request authorization and protected output."""
import logging
import os
import uuid

from django.core.files.storage import default_storage
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from rest_framework.response import Response
from rest_framework.views import APIView

from DiagnosticosIA.models import AIAnalysisRun
from DiagnosticosIA.runs import AnalysisClinicConflict, AnalysisKeyConflict
from DiagnosticosIA.services import ClinicalImageChangedError, ClinicalImageMissingError, analyze_clinical_image_detached
from DiagnosticosIA.tenant_runs import AnalysisInterrupted, execute_tenant_analysis
from .tenant_images import TenantClinicalImageSerializer, image_for
from .clinic_context import TenantClinicalContextMixin
from .throttles import ExpensiveThrottle
from .pagination import ClinicalPagination
from .features import TenantAIFeatureMixin

logger = logging.getLogger(__name__)


@method_decorator(never_cache, name='dispatch')
class TenantAnalyzeImage(TenantAIFeatureMixin, TenantClinicalContextMixin, APIView):
    throttle_classes = [ExpensiveThrottle]

    def post(self, request, image_id):
        if any(field in request.data for field in ('clinic', 'clinic_id', 'medico', 'medico_id', 'paciente', 'paciente_id')):
            return Response({'detail': 'La clínica, el médico y el paciente se asignan desde el contexto autorizado.'}, status=400)
        force = request.data.get('force', False)
        if not isinstance(force, bool):
            return Response({'detail': 'force debe ser booleano.'}, status=400)
        try:
            key = uuid.UUID(request.headers['Idempotency-Key']) if request.headers.get('Idempotency-Key') else None
        except ValueError:
            return Response({'detail': 'Idempotency-Key inválida.'}, status=400)
        try:
            run, disposition = execute_tenant_analysis(user=request.user, clinic_id=self.membership.clinic_id,
                                                       image_id=image_id, request_id=request._request.request_id,
                                                       force=force, idempotency_key=key,
                                                       analyzer=analyze_clinical_image_detached)
        except ClinicalImageMissingError:
            return Response({'detail': 'La imagen original no está disponible.', 'code': 'source_image_missing'}, status=404)
        except ClinicalImageChangedError:
            return Response({'detail': 'La imagen cambió durante el análisis.'}, status=409)
        except AnalysisKeyConflict:
            return Response({'detail': 'La clave ya corresponde a otro análisis.'}, status=409)
        except AnalysisClinicConflict:
            return Response({'detail': 'El historial del análisis requiere conciliación.'}, status=409)
        except AnalysisInterrupted:
            return Response({'detail': 'La ejecución fue interrumpida.'}, status=409)
        except Exception as exc:
            # DRF permission/404 exceptions must retain their normal response.
            from django.http import Http404
            from rest_framework.exceptions import APIException
            if isinstance(exc, (Http404, APIException)):
                raise
            logger.error('Fallo de análisis IA request_id=%s', request._request.request_id)
            return Response({'detail': 'No se pudo analizar la imagen. Inténtalo de nuevo.'}, status=500)
        if run.status == AIAnalysisRun.FAILED:
            return Response({'detail': 'La ejecución anterior falló. Solicita un nuevo análisis.', 'run_id': run.pk}, status=409)
        image = image_for(request, self.membership.clinic_id, image_id)
        if disposition == 'reused' and (not run.result_name or image.resultados.name != run.result_name or not default_storage.exists(run.result_name)):
            return Response({'detail': 'El resultado de esa ejecución no está disponible como resultado actual.', 'run_id': run.pk}, status=409)
        return Response({'image': TenantClinicalImageSerializer(image).data, 'detections': run.detections,
                         'run_id': run.pk, 'status': run.status, 'disposition': disposition},
                        status=202 if disposition == 'running' else 200)


@method_decorator(never_cache, name='dispatch')
class TenantAnalysisRuns(TenantAIFeatureMixin, TenantClinicalContextMixin, APIView):
    def get(self, request, image_id):
        image = image_for(request, self.membership.clinic_id, image_id)
        rows = image.analysis_runs.filter(clinic_id=self.membership.clinic_id).order_by('-requested_at', '-pk')
        paginator = ClinicalPagination()
        page = paginator.paginate_queryset(rows, request, view=self)
        data = [{'id': run.pk, 'status': run.status, 'requested_by': run.requested_by_id,
                 'requested_at': run.requested_at, 'started_at': run.started_at, 'completed_at': run.completed_at,
                 'model_name': run.model_name, 'model_version': run.model_version,
                 'explicit_reanalysis': run.explicit_reanalysis, 'failure_category': run.failure_category,
                 'has_result': bool(run.result_name)} for run in page]
        self.record(image, 'TENANT_AI_RUN_LIST_VIEWED', 'image')
        return paginator.get_paginated_response(data)


@method_decorator(never_cache, name='dispatch')
class TenantAnalysisRunFile(TenantAIFeatureMixin, TenantClinicalContextMixin, APIView):
    def get(self, request, image_id, run_id):
        image = image_for(request, self.membership.clinic_id, image_id)
        if image.analysis_runs.exclude(clinic_id=self.membership.clinic_id).exists():
            return Response({'detail': 'Archivo no disponible.'}, status=404)
        run = get_object_or_404(AIAnalysisRun, pk=run_id, image=image, clinic_id=self.membership.clinic_id,
                                status=AIAnalysisRun.SUCCEEDED)
        if not run.result_name:
            return Response({'detail': 'Archivo no disponible.'}, status=404)
        try:
            opened = default_storage.open(run.result_name, 'rb')
        except FileNotFoundError:
            return Response({'detail': 'Archivo no disponible.'}, status=404)
        try:
            self.record(run, 'TENANT_AI_RESULT_VIEWED', 'ai_run')
        except Exception:
            opened.close()
            raise
        response = FileResponse(opened, as_attachment=True, filename=os.path.basename(run.result_name))
        response['Cache-Control'] = 'private, no-store'
        return response

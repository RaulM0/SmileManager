"""Tenant-scoped clinical image upload, listing and protected downloads."""
import logging
import os

from django.db import transaction
from django.db.models import Exists, OuterRef
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from rest_framework.exceptions import ValidationError
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from DiagnosticosIA.models import AIAnalysisRun
from Pacientes.models import ImagenesClinicas
from .policies import clinic_clinical_queryset
from .serializers import ClinicalImageSerializer
from .tenant_consultations import patient_for
from .tenant_patients import TenantClinicalContextMixin
from .views import ClinicalPagination, PatientPagination
from .features import TenantAIFeatureMixin, ai_enabled_for_clinic, require_ai_enabled

logger = logging.getLogger(__name__)


class TenantClinicalImageSerializer(ClinicalImageSerializer):
    def to_internal_value(self, data):
        if any(field in data for field in ('clinic', 'clinic_id', 'medico', 'medico_id', 'paciente', 'paciente_id')):
            raise ValidationError({'detail': 'La clínica, el médico y el paciente se asignan desde el contexto autorizado.'})
        return super().to_internal_value(data)

    def get_imagen_url(self, image):
        return reverse('tenant-clinical-image-file', args=[image.pk, 'original']) if image.imagen else None

    def get_resultados_url(self, image):
        valid = ai_enabled_for_clinic(image.paciente.clinic) and image.resultados and getattr(image, 'tenant_has_result', False)
        return reverse('tenant-clinical-image-file', args=[image.pk, 'result']) if valid else None


def image_rows(request, clinic_id):
    matching_results = AIAnalysisRun.objects.filter(image_id=OuterRef('pk'), clinic_id=clinic_id,
                                                    status=AIAnalysisRun.SUCCEEDED, result_name=OuterRef('resultados')).exclude(result_name='')
    inconsistent_runs = AIAnalysisRun.objects.filter(image_id=OuterRef('pk')).exclude(clinic_id=clinic_id)
    return clinic_clinical_queryset(request.user, clinic_id, ImagenesClinicas).select_related('paciente', 'consulta').annotate(
        tenant_has_result=Exists(matching_results) & ~Exists(inconsistent_runs),
    )


def image_for(request, clinic_id, image_id):
    return get_object_or_404(image_rows(request, clinic_id), pk=image_id)


@method_decorator(never_cache, name='dispatch')
class TenantClinicalImages(TenantClinicalContextMixin, APIView):
    def get(self, request, patient_id):
        patient = patient_for(request, self.membership.clinic_id, patient_id)
        images = image_rows(request, self.membership.clinic_id).filter(paciente=patient).order_by('-fecha_subida', '-pk')
        if request.query_params.get('date'):
            value = serializers.DateField().run_validation(request.query_params['date'])
            images = images.filter(fecha_subida__date=value)
        if request.query_params.get('consultation_id'):
            value = serializers.IntegerField(min_value=1).run_validation(request.query_params['consultation_id'])
            images = images.filter(consulta_id=value)
        paginator = ClinicalPagination()
        page = paginator.paginate_queryset(images, request, view=self)
        data = TenantClinicalImageSerializer(page, many=True).data
        self.record(patient, 'TENANT_CLINICAL_IMAGE_LIST_VIEWED')
        return paginator.get_paginated_response(data)

    def post(self, request, patient_id):
        image = None
        try:
            with transaction.atomic():
                self.lock_context()
                patient = patient_for(request, self.membership.clinic_id, patient_id, lock=True)
                serializer = TenantClinicalImageSerializer(data=request.data, context={'request': request, 'patient': patient, 'clinic_id': self.membership.clinic_id})
                serializer.is_valid(raise_exception=True)
                image = serializer.save()
                self.record(image, 'TENANT_CLINICAL_IMAGE_CREATED', 'image')
                data = serializer.data
        except Exception:
            if image is not None and image.imagen:
                try:
                    image.imagen.delete(save=False)
                except Exception:
                    logger.exception('No fue posible limpiar un archivo clínico después de un error de transacción.')
            raise
        return Response(data, status=201)


@method_decorator(never_cache, name='dispatch')
class TenantClinicalImageDetail(TenantClinicalContextMixin, APIView):
    def get(self, request, image_id):
        image = image_for(request, self.membership.clinic_id, image_id)
        data = TenantClinicalImageSerializer(image).data
        self.record(image, 'TENANT_CLINICAL_IMAGE_VIEWED', 'image')
        return Response(data)

    @transaction.atomic
    def delete(self, request, image_id):
        self.lock_context()
        images = image_rows(request, self.membership.clinic_id).select_for_update(of=('self',))
        image = get_object_or_404(images, pk=image_id)
        image.is_active = False
        image.save(update_fields=['is_active'])
        self.record(image, 'TENANT_CLINICAL_IMAGE_ARCHIVED', 'image')
        return Response(status=204)


@method_decorator(never_cache, name='dispatch')
class TenantClinicalImageFile(TenantClinicalContextMixin, APIView):
    def get(self, request, image_id, kind):
        if kind == 'result':
            require_ai_enabled(self.membership.clinic)
        image = image_for(request, self.membership.clinic_id, image_id)
        if kind == 'original':
            file = image.imagen
        elif kind == 'result' and image.resultados and image.tenant_has_result:
            file = image.resultados
        else:
            return Response({'detail': 'Archivo no disponible.'}, status=404)
        if not file:
            return Response({'detail': 'Archivo no disponible.'}, status=404)
        try:
            opened = file.open('rb')
        except FileNotFoundError:
            return Response({'detail': 'Archivo no disponible.'}, status=404)
        try:
            self.record(image, 'TENANT_CLINICAL_FILE_VIEWED', 'image')
        except Exception:
            opened.close()
            raise
        response = FileResponse(opened, as_attachment=True, filename=os.path.basename(file.name))
        response['Cache-Control'] = 'private, no-store'
        return response


@method_decorator(never_cache, name='dispatch')
class TenantDiagnostics(TenantAIFeatureMixin, TenantClinicalContextMixin, APIView):
    def get(self, request):
        images = image_rows(request, self.membership.clinic_id).order_by('-fecha_subida', '-pk')
        patient = request.query_params.get('patient', '').strip()[:150]
        image_type = request.query_params.get('type', '').strip()[:150]
        date = request.query_params.get('date', '')
        if patient:
            images = images.filter(paciente__nombre__icontains=patient)
        if image_type:
            images = images.filter(tipo_imagen=image_type)
        if date:
            images = images.filter(fecha_subida__date=serializers.DateField().run_validation(date))
        total = images.count()
        processed = images.filter(tenant_has_result=True).count()
        types = images.values('tipo_imagen').distinct().count()
        paginator = PatientPagination()
        page = paginator.paginate_queryset(images, request, view=self)
        data = TenantClinicalImageSerializer(page, many=True).data
        from Usuarios.models import AuditEvent
        AuditEvent.objects.create(actor=request.user, clinic_id=self.membership.clinic_id,
                                  action='TENANT_DIAGNOSTICS_VIEWED', resource_type='images',
                                  request_id=request._request.request_id)
        response = paginator.get_paginated_response(data)
        response.data['statistics'] = {'total': total, 'processed': processed, 'pending': total - processed,
                                       'processed_percentage': round(processed / total * 100, 2) if total else 0,
                                       'type_count': types}
        return response

"""Tenant-scoped comparative studies and protected study files."""
import logging
import os

from django.db import transaction
from django.http import FileResponse, Http404
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from Pacientes.PDF import render_pdf_progreso
from Pacientes.models import EstudioComparativo
from Pacientes.access import consistent_or_404
from .serializers import ComparativeStudySerializer, STUDY_IMAGE_FIELDS
from .services.clinical_records import ClinicalDataConflict
from .tenant_consultations import patient_for
from .clinic_context import TenantClinicalContextMixin

logger = logging.getLogger(__name__)


class TenantStudySerializer(ComparativeStudySerializer):
    def get_image_urls(self, study):
        return {field: reverse('tenant-study-image', args=[study.paciente_id, field]) if getattr(study, field) else None
                for field in STUDY_IMAGE_FIELDS}


class TenantStudyMixin(TenantClinicalContextMixin):
    def study_for(self, patient, *, lock=False):
        rows = consistent_or_404(self.request.user, EstudioComparativo, patient, clinic_id=self.membership.clinic_id)
        if lock:
            rows = rows.select_for_update(of=('self',))
        results = list(rows.order_by('-fecha_creacion', '-pk')[:2])
        if len(results) > 1:
            raise ClinicalDataConflict('Los estudios duplicados requieren conciliación.')
        return results[0] if results else None


@method_decorator(never_cache, name='dispatch')
class TenantComparativeStudy(TenantStudyMixin, APIView):
    def get(self, request, patient_id):
        patient = patient_for(request, self.membership.clinic_id, patient_id)
        study = self.study_for(patient)
        data = {'exists': False} if study is None else {'exists': True, **TenantStudySerializer(study).data}
        self.record(patient, 'TENANT_STUDY_VIEWED')
        return Response(data)

    def put(self, request, patient_id):
        study = None
        assigned = set()
        old_names = {}
        try:
            with transaction.atomic():
                self.lock_context()
                if any(field in request.data for field in ('clinic', 'clinic_id', 'medico', 'medico_id', 'paciente', 'paciente_id')):
                    raise ValidationError({'detail': 'La clínica, el médico y el paciente se asignan desde el contexto autorizado.'})
                patient = patient_for(request, self.membership.clinic_id, patient_id, lock=True)
                study = self.study_for(patient, lock=True)
                serializer = TenantStudySerializer(study, data=request.data, partial=study is not None)
                serializer.is_valid(raise_exception=True)
                if study is None:
                    study = EstudioComparativo(paciente=patient, medico=request.user)
                for field in STUDY_IMAGE_FIELDS:
                    file = getattr(study, field)
                    old_names[field] = file.name if file else None
                assigned = set(serializer.validated_data).intersection(STUDY_IMAGE_FIELDS)
                for field, value in serializer.validated_data.items():
                    setattr(study, field, value)
                study.save()
                self.record(patient, 'TENANT_STUDY_UPDATED')
                data = TenantStudySerializer(study).data
        except Exception:
            if study is not None:
                for field in assigned:
                    file = getattr(study, field)
                    if file and file._committed and file.name != old_names.get(field):
                        try:
                            file.delete(save=False)
                        except Exception:
                            logger.exception('No fue posible limpiar un archivo de estudio después de un error de transacción.')
            raise
        return Response({'exists': True, **data})


@method_decorator(never_cache, name='dispatch')
class TenantStudyImage(TenantStudyMixin, APIView):
    def get(self, request, patient_id, field):
        patient = patient_for(request, self.membership.clinic_id, patient_id)
        if field not in STUDY_IMAGE_FIELDS:
            raise Http404
        study = self.study_for(patient)
        file = getattr(study, field, None) if study else None
        if not file:
            raise Http404
        try:
            opened = file.open('rb')
        except FileNotFoundError as exc:
            raise Http404 from exc
        try:
            self.record(patient, 'TENANT_STUDY_IMAGE_VIEWED')
        except Exception:
            opened.close()
            raise
        response = FileResponse(opened, filename=os.path.basename(file.name))
        response['Cache-Control'] = 'private, no-store'
        return response


@method_decorator(never_cache, name='dispatch')
class TenantStudyPDF(TenantStudyMixin, APIView):
    def get(self, request, patient_id):
        patient = patient_for(request, self.membership.clinic_id, patient_id)
        study = self.study_for(patient)
        response = render_pdf_progreso(patient, study)
        if response.status_code == 200:
            self.record(patient, 'TENANT_STUDY_PDF_VIEWED')
        response['Cache-Control'] = 'private, no-store'
        return response

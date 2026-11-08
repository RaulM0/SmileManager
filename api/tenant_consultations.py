"""Tenant-scoped consultation reads and creation."""
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from Pacientes.models import Consulta, Paciente
from .policies import clinic_clinical_queryset
from .serializers import ConsultationSerializer
from .tenant_patients import TenantClinicalContextMixin
from .views import ClinicalPagination


def patient_for(request, clinic_id, patient_id, *, lock=False):
    patients = clinic_clinical_queryset(request.user, clinic_id, Paciente)
    if lock:
        patients = patients.select_for_update(of=('self',))
    return get_object_or_404(patients, pk=patient_id)


@method_decorator(never_cache, name='dispatch')
class TenantConsultations(TenantClinicalContextMixin, APIView):
    def get(self, request, patient_id):
        patient = patient_for(request, self.membership.clinic_id, patient_id)
        rows = clinic_clinical_queryset(request.user, self.membership.clinic_id, Consulta).filter(paciente=patient).select_related('paciente').order_by('-fecha_consulta', '-pk')
        paginator = ClinicalPagination()
        page = paginator.paginate_queryset(rows, request, view=self)
        data = ConsultationSerializer(page, many=True).data
        self.record(patient, 'TENANT_CONSULTATION_LIST_VIEWED')
        return paginator.get_paginated_response(data)

    @transaction.atomic
    def post(self, request, patient_id):
        self.lock_context()
        if any(field in request.data for field in ('clinic', 'clinic_id', 'medico', 'medico_id', 'paciente', 'paciente_id')):
            raise ValidationError({'detail': 'La clínica, el médico y el paciente se asignan desde el contexto autorizado.'})
        patient = patient_for(request, self.membership.clinic_id, patient_id, lock=True)
        serializer = ConsultationSerializer(data=request.data, context={'request': request, 'patient': patient, 'clinic_id': self.membership.clinic_id})
        serializer.is_valid(raise_exception=True)
        consultation = serializer.save()
        self.record(consultation, 'TENANT_CONSULTATION_CREATED', 'consultation')
        return Response(serializer.data, status=201)


@method_decorator(never_cache, name='dispatch')
class TenantConsultationDetail(TenantClinicalContextMixin, APIView):
    def get(self, request, consultation_id):
        rows = clinic_clinical_queryset(request.user, self.membership.clinic_id, Consulta).select_related('paciente')
        consultation = get_object_or_404(rows, pk=consultation_id)
        data = ConsultationSerializer(consultation).data
        self.record(consultation, 'TENANT_CONSULTATION_VIEWED', 'consultation')
        return Response(data)

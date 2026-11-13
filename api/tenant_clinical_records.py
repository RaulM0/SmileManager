"""Tenant-scoped medical history and odontogram endpoints."""
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from Pacientes.models import AntescedentesMedicos, Odontograma, Paciente
from Pacientes.access import clinic_clinical_queryset, consistent_or_404
from .serializers import MedicalHistorySerializer, OdontogramSerializer
from .services.clinical_records import save_record
from .clinic_context import TenantClinicalContextMixin


class TenantClinicalRecordMixin(TenantClinicalContextMixin):
    def patient(self, patient_id):
        return get_object_or_404(clinic_clinical_queryset(self.request.user, self.membership.clinic_id, Paciente), pk=patient_id)

    def rows(self, model, patient):
        return consistent_or_404(self.request.user, model, patient, clinic_id=self.membership.clinic_id)

    def validate_ownership_fields(self, data):
        if any(field in data for field in ('clinic', 'clinic_id', 'medico', 'medico_id', 'paciente', 'paciente_id')):
            raise ValidationError({'detail': 'La clínica, el médico y el paciente se asignan desde el contexto autorizado.'})


@method_decorator(never_cache, name='dispatch')
class TenantMedicalHistory(TenantClinicalRecordMixin, APIView):
    def get(self, request, patient_id):
        patient = self.patient(patient_id)
        history = self.rows(AntescedentesMedicos, patient).first() or AntescedentesMedicos(paciente=patient, medico=request.user)
        data = MedicalHistorySerializer(history).data
        self.record(patient, 'TENANT_CLINICAL_HISTORY_VIEWED')
        return Response(data)

    @transaction.atomic
    def put(self, request, patient_id):
        self.lock_context()
        self.validate_ownership_fields(request.data)
        patient = self.patient(patient_id)
        history = self.rows(AntescedentesMedicos, patient).first() or AntescedentesMedicos(paciente=patient, medico=request.user)
        serializer = MedicalHistorySerializer(history, data=request.data)
        serializer.is_valid(raise_exception=True)
        history = save_record(user=request.user, clinic_id=self.membership.clinic_id, patient_id=patient_id,
                              model=AntescedentesMedicos, changes=serializer.validated_data,
                              expected_version=request.data.get('version'))
        self.record(patient, 'TENANT_CLINICAL_HISTORY_UPDATED')
        return Response(MedicalHistorySerializer(history).data)


@method_decorator(never_cache, name='dispatch')
class TenantOdontogram(TenantClinicalRecordMixin, APIView):
    def get(self, request, patient_id):
        patient = self.patient(patient_id)
        odontogram = self.rows(Odontograma, patient).order_by('-created').first()
        data = OdontogramSerializer(odontogram).data if odontogram else {
            'id': None, 'denticion_permanente': {}, 'denticion_decidua': {},
            'resumen': {}, 'created': None, 'updated': None, 'version': 0,
        }
        self.record(patient, 'TENANT_ODONTOGRAM_VIEWED')
        return Response(data)

    @transaction.atomic
    def put(self, request, patient_id):
        self.lock_context()
        self.validate_ownership_fields(request.data)
        patient = self.patient(patient_id)
        odontogram = self.rows(Odontograma, patient).first() or Odontograma(paciente=patient, medico=request.user)
        serializer = OdontogramSerializer(odontogram, data=request.data)
        serializer.is_valid(raise_exception=True)
        odontogram = save_record(user=request.user, clinic_id=self.membership.clinic_id, patient_id=patient_id,
                                 model=Odontograma, changes=serializer.validated_data,
                                 expected_version=request.data.get('version'))
        self.record(patient, 'TENANT_ODONTOGRAM_UPDATED')
        return Response(OdontogramSerializer(odontogram).data)

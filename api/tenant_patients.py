"""Patient API with explicit clinic context and assigned-doctor policy.

Legacy patient routes remain separate and must not be used for multi-clinic
operation until their migration and enforcement have been completed.
"""
from django.db import transaction
from django.db.models import Q, Value
from django.db.models.functions import Concat
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from rest_framework import generics, serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from Pacientes.models import Paciente
from Usuarios.models import AuditEvent
from .policies import clinic_clinical_queryset
from .serializers import PatientSerializer
from .services.patients import deactivate_patient
from .tenant_context import lock_clinic_capability, require_clinic_capability
from .views import PatientPagination


class TenantPatientSerializer(PatientSerializer):
    def to_internal_value(self, data):
        if 'clinic' in data or 'clinic_id' in data or 'medico' in data or 'medico_id' in data:
            raise serializers.ValidationError({'detail': 'La clínica y el médico se asignan desde el contexto autorizado.'})
        return super().to_internal_value(data)


class TenantClinicalContextMixin:
    permission_classes = [IsAuthenticated]

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        self.membership = require_clinic_capability(request.user, request.headers.get('X-Clinic-ID'), 'clinical.assigned')

    def lock_context(self):
        """Serialize writes with clinic and membership transitions using their lock order."""
        self.membership = lock_clinic_capability(self.request.user, self.membership.clinic_id, 'clinical.assigned')
        return self.membership.clinic

    def record(self, resource, action, resource_type='patient'):
        AuditEvent.objects.create(actor=self.request.user, clinic_id=self.membership.clinic_id,
                                  action=action, resource_type=resource_type, resource_id=str(resource.pk),
                                  request_id=self.request._request.request_id)


class TenantPatientMixin(TenantClinicalContextMixin):
    serializer_class = TenantPatientSerializer

    def get_serializer_context(self):
        return {**super().get_serializer_context(), 'clinic_id': self.membership.clinic_id}

    def get_queryset(self):
        qs = clinic_clinical_queryset(self.request.user, self.membership.clinic_id, Paciente).order_by('appat', 'pk')
        search = self.request.query_params.get('search', '').strip()[:150]
        if search:
            qs = qs.annotate(full_name=Concat('nombre', Value(' '), 'appat', Value(' '), 'apmat')).filter(
                Q(nombre__icontains=search) | Q(appat__icontains=search) | Q(apmat__icontains=search)
                | Q(telefono__icontains=search) | Q(email__icontains=search) | Q(full_name__icontains=search))
        if self.request.method in ('PUT', 'PATCH'):
            qs = qs.select_for_update(of=('self',))
        return qs


@method_decorator(never_cache, name='dispatch')
class TenantPatientList(TenantPatientMixin, generics.ListCreateAPIView):
    pagination_class = PatientPagination

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        AuditEvent.objects.create(actor=request.user, clinic_id=self.membership.clinic_id,
                                  action='TENANT_PATIENT_LIST_VIEWED', resource_type='patients',
                                  request_id=request._request.request_id)
        return response

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        self.lock_context()
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        patient = serializer.save(clinic_id=self.membership.clinic_id)
        self.record(patient, 'TENANT_PATIENT_CREATED')


@method_decorator(never_cache, name='dispatch')
class TenantPatientDetail(TenantPatientMixin, generics.RetrieveUpdateAPIView):
    def retrieve(self, request, *args, **kwargs):
        patient = self.get_object()
        data = self.get_serializer(patient).data
        self.record(patient, 'TENANT_PATIENT_VIEWED')
        return Response(data)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        self.lock_context()
        return super().update(request, *args, **kwargs)

    def perform_update(self, serializer):
        patient = serializer.save()
        self.record(patient, 'TENANT_PATIENT_UPDATED')


@method_decorator(never_cache, name='dispatch')
class TenantPatientAutocomplete(TenantPatientMixin, APIView):
    def get(self, request):
        term = request.query_params.get('term', '').strip()[:150]
        rows = self.get_queryset().annotate(full_name=Concat('nombre', Value(' '), 'appat', Value(' '), 'apmat'))
        query = Q(nombre__icontains=term) | Q(appat__icontains=term) | Q(apmat__icontains=term) | Q(full_name__icontains=term) | Q(telefono__icontains=term)
        if term.isdigit() and len(term) <= 18:
            query |= Q(id=int(term))
        patients = rows.filter(query)[:10]
        data = {'results': [{'id': patient.pk, 'text': f'{patient.nombre} {patient.appat} {patient.apmat}'} for patient in patients]}
        AuditEvent.objects.create(actor=request.user, clinic_id=self.membership.clinic_id,
                                  action='TENANT_PATIENT_SEARCHED', resource_type='patients',
                                  request_id=request._request.request_id)
        return Response(data)


@method_decorator(never_cache, name='dispatch')
class TenantPatientDeactivate(TenantPatientMixin, APIView):
    @transaction.atomic
    def post(self, request, pk):
        self.lock_context()
        patient = get_object_or_404(self.get_queryset().select_for_update(of=('self',)), pk=pk)
        deactivate_patient(patient=patient, user=request.user, clinic_id=self.membership.clinic_id)
        self.record(patient, 'TENANT_PATIENT_DEACTIVATED')
        return Response(TenantPatientSerializer(patient).data)

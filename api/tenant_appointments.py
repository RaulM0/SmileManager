"""Appointment API with explicit clinic and assigned-doctor authorization."""
from django.db import transaction
from django.conf import settings
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_date
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from rest_framework import generics, serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from Citas.models import Cita
from Pacientes.models import Paciente
from Usuarios.models import AuditEvent
from .policies import clinic_clinical_queryset
from .serializers import AppointmentSerializer
from .services.appointments import save_appointment, transition_appointment
from .tenant_patients import TenantClinicalContextMixin
from .views import ClinicalPagination


class TenantAppointmentSerializer(AppointmentSerializer):
    def to_internal_value(self, data):
        if any(field in data for field in ('clinic', 'clinic_id', 'medico', 'medico_id')):
            raise serializers.ValidationError({'detail': 'La clínica y el médico se asignan desde el contexto autorizado.'})
        return super().to_internal_value(data)

    def validate_paciente_id(self, value):
        view = self.context['view']
        if not clinic_clinical_queryset(self.context['request'].user, view.membership.clinic_id, Paciente).filter(pk=value).exists():
            raise serializers.ValidationError('Paciente no encontrado.')
        return value

    def create(self, validated_data):
        view = self.context['view']
        user = self.context['request'].user
        patient_id = validated_data.pop('paciente_id')
        patient = get_object_or_404(clinic_clinical_queryset(user, view.membership.clinic_id, Paciente), pk=patient_id)
        return save_appointment(user=user, patient=patient, validated_data=validated_data, clinic_id=view.membership.clinic_id)

    def update(self, instance, validated_data):
        view = self.context['view']
        user = self.context['request'].user
        patient_id = validated_data.pop('paciente_id', None)
        patient = get_object_or_404(clinic_clinical_queryset(user, view.membership.clinic_id, Paciente), pk=patient_id) if patient_id is not None else None
        return save_appointment(user=user, appointment=instance, patient=patient, validated_data=validated_data, clinic_id=view.membership.clinic_id)


class TenantAppointmentMixin(TenantClinicalContextMixin):
    serializer_class = TenantAppointmentSerializer

    def get_queryset(self):
        rows = clinic_clinical_queryset(self.request.user, self.membership.clinic_id, Cita).select_related('paciente').order_by('fecha', 'hora', 'pk')
        start, end = self.request.query_params.get('from'), self.request.query_params.get('to')
        if start or end:
            try:
                start_date, end_date = parse_date(start or ''), parse_date(end or '')
            except ValueError:
                start_date = end_date = None
            if not start_date or not end_date or start_date > end_date or (end_date-start_date).days + 1 > settings.APPOINTMENT_MAX_RANGE_DAYS:
                raise serializers.ValidationError({'detail': 'Indica un rango de fechas válido dentro del límite permitido.'})
            rows = rows.filter(fecha__range=(start_date, end_date))
        status = self.request.query_params.get('status', '')
        if status:
            rows = rows.filter(estatus=status)
        search = self.request.query_params.get('search', '').strip()[:150]
        if search:
            query = Q(paciente__nombre__icontains=search) | Q(paciente__appat__icontains=search) | Q(paciente__telefono__icontains=search)
            if search.isdigit() and len(search) <= 18:
                query |= Q(id=int(search))
            rows = rows.filter(query)
        if self.request.method in ('PUT', 'PATCH'):
            rows = rows.select_for_update(of=('self',))
        return rows


@method_decorator(never_cache, name='dispatch')
class TenantAppointmentList(TenantAppointmentMixin, generics.ListCreateAPIView):
    pagination_class = ClinicalPagination

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        AuditEvent.objects.create(actor=request.user, clinic_id=self.membership.clinic_id,
                                  action='TENANT_APPOINTMENT_LIST_VIEWED', resource_type='appointments',
                                  request_id=request._request.request_id)
        return response

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        self.lock_context()
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        appointment = serializer.save()
        self.record(appointment, 'TENANT_APPOINTMENT_CREATED', 'appointment')


@method_decorator(never_cache, name='dispatch')
class TenantAppointmentDetail(TenantAppointmentMixin, generics.RetrieveUpdateAPIView):
    def retrieve(self, request, *args, **kwargs):
        appointment = self.get_object()
        data = self.get_serializer(appointment).data
        self.record(appointment, 'TENANT_APPOINTMENT_VIEWED', 'appointment')
        return Response(data)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        self.lock_context()
        return super().update(request, *args, **kwargs)

    def perform_update(self, serializer):
        appointment = serializer.save()
        self.record(appointment, 'TENANT_APPOINTMENT_UPDATED', 'appointment')


@method_decorator(never_cache, name='dispatch')
class TenantAppointmentTransition(TenantAppointmentMixin, APIView):
    @transaction.atomic
    def post(self, request, pk, operation):
        targets = {'complete': 'C', 'cancel': 'A'}
        if operation not in targets:
            return Response({'detail': 'Operación no disponible.'}, status=404)
        self.lock_context()
        appointment = get_object_or_404(self.get_queryset(), pk=pk)
        appointment = transition_appointment(user=request.user, clinic_id=self.membership.clinic_id,
                                             appointment=appointment, target=targets[operation])
        self.record(appointment, 'TENANT_APPOINTMENT_TRANSITIONED', 'appointment')
        return Response(TenantAppointmentSerializer(appointment).data)

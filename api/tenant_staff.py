"""Reception agenda: same-clinic scheduling without access to clinical records."""
from django.db import transaction
from django.db.models import Exists, OuterRef, Q
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from Citas.models import Cita
from Pacientes.models import Paciente
from Usuarios.models import AuditEvent, ClinicMembership
from .services.appointments import can_transition, validate_appointment_schedule, InvalidStateTransition
from Usuarios.clinic_context import require_clinic_capability, lock_clinic_capability
from .pagination import ClinicalPagination


def schedulable_patients(clinic_id):
    doctors = ClinicMembership.objects.filter(
        clinic_id=clinic_id, user_id=OuterRef('medico_id'), role='DOCTOR',
        status='ACTIVE', user__is_active=True, clinic__status='ACTIVE',
    )
    return Paciente.objects.filter(clinic_id=clinic_id, estatus='A').alias(
        _doctor_active=Exists(doctors),
    ).filter(_doctor_active=True)


def patient_summary(patient):
    return {'id': patient.pk, 'name': f'{patient.nombre} {patient.appat} {patient.apmat}',
            'doctor': patient.medico.get_full_name() or patient.medico.username}


def appointment_data(appointment):
    return {'id': appointment.pk, 'patient': patient_summary(appointment.paciente),
            'fecha': appointment.fecha, 'hora': appointment.hora,
            'motivo': appointment.motivo, 'estatus': appointment.estatus}


class AppointmentInput(serializers.Serializer):
    paciente_id = serializers.IntegerField(min_value=1)
    fecha = serializers.DateField()
    hora = serializers.TimeField()
    motivo = serializers.CharField(max_length=1000, allow_blank=True, default='')

    def validate(self, values):
        if set(self.initial_data) - set(self.fields):
            raise serializers.ValidationError('Solo se permiten paciente_id, fecha, hora y motivo.')
        return values


class StaffContext:
    permission_classes = [IsAuthenticated]

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        self.membership = require_clinic_capability(request.user, request.headers.get('X-Clinic-ID'), 'appointments.manage')

    def lock(self):
        self.membership = lock_clinic_capability(self.request.user, self.membership.clinic_id, 'appointments.manage')

    def rows(self):
        return Cita.objects.filter(paciente__in=schedulable_patients(self.membership.clinic_id)).select_related('paciente__medico').order_by('fecha', 'hora', 'pk')

    def record(self, action, resource_id='', resource_type='appointment'):
        AuditEvent.objects.create(actor=self.request.user, clinic_id=self.membership.clinic_id,
                                  action=action, resource_type=resource_type, resource_id=str(resource_id),
                                  request_id=self.request._request.request_id)


@method_decorator(never_cache, name='dispatch')
class StaffPatients(StaffContext, APIView):
    def get(self, request):
        term = request.query_params.get('term', '').strip()[:150]
        rows = schedulable_patients(self.membership.clinic_id).select_related('medico')
        if term:
            rows = rows.filter(Q(nombre__icontains=term) | Q(appat__icontains=term) | Q(apmat__icontains=term))
        self.record('TENANT_STAFF_PATIENT_LOOKUP', resource_type='patient_directory')
        return Response({'results': [patient_summary(row) for row in rows.order_by('appat', 'pk')[:20]]})


@method_decorator(never_cache, name='dispatch')
class StaffAppointments(StaffContext, APIView):
    def get(self, request):
        rows = self.rows()
        if request.query_params.get('date'):
            date = serializers.DateField().run_validation(request.query_params['date'])
            rows = rows.filter(fecha=date)
        state = request.query_params.get('status')
        if state:
            if state not in ('P', 'C', 'A'):
                raise serializers.ValidationError({'status': 'Estado no válido.'})
            rows = rows.filter(estatus=state)
        paginator = ClinicalPagination()
        page = paginator.paginate_queryset(rows, request, view=self)
        self.record('TENANT_STAFF_APPOINTMENT_LIST_VIEWED', resource_type='appointments')
        return paginator.get_paginated_response([appointment_data(row) for row in page])

    @transaction.atomic
    def post(self, request):
        self.lock()
        serializer = AppointmentInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        values = dict(serializer.validated_data)
        patient = get_object_or_404(schedulable_patients(self.membership.clinic_id).select_for_update(of=('self',)).select_related('medico'), pk=values.pop('paciente_id'))
        validate_appointment_schedule(values['fecha'], values['hora'])
        appointment = Cita.objects.create(paciente=patient, **values)
        self.record('TENANT_STAFF_APPOINTMENT_CREATED', appointment.pk)
        return Response(appointment_data(appointment), status=201)


@method_decorator(never_cache, name='dispatch')
class StaffAppointmentDetail(StaffContext, APIView):
    def get(self, request, pk):
        appointment = get_object_or_404(self.rows(), pk=pk)
        self.record('TENANT_STAFF_APPOINTMENT_VIEWED', appointment.pk)
        return Response(appointment_data(appointment))

    @transaction.atomic
    def patch(self, request, pk):
        self.lock()
        appointment = get_object_or_404(self.rows().select_for_update(of=('self',)), pk=pk)
        serializer = AppointmentInput(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        values = dict(serializer.validated_data)
        if 'paciente_id' in values:
            appointment.paciente = get_object_or_404(schedulable_patients(self.membership.clinic_id).select_related('medico').select_for_update(of=('self',)), pk=values.pop('paciente_id'))
        for field, value in values.items():
            setattr(appointment, field, value)
        validate_appointment_schedule(appointment.fecha, appointment.hora)
        appointment.save()
        self.record('TENANT_STAFF_APPOINTMENT_UPDATED', appointment.pk)
        return Response(appointment_data(appointment))


@method_decorator(never_cache, name='dispatch')
class StaffAppointmentTransition(StaffContext, APIView):
    @transaction.atomic
    def post(self, request, pk, operation):
        target = {'complete': 'C', 'cancel': 'A'}.get(operation)
        if target is None:
            return Response(status=404)
        if request.data:
            raise serializers.ValidationError('Esta operación no recibe campos adicionales.')
        self.lock()
        appointment = get_object_or_404(self.rows().select_for_update(of=('self',)), pk=pk)
        if not can_transition(appointment.estatus, target):
            raise InvalidStateTransition()
        appointment.estatus = target
        appointment.save(update_fields=['estatus', 'updated'])
        self.record('TENANT_STAFF_APPOINTMENT_TRANSITIONED', appointment.pk)
        return Response(appointment_data(appointment))

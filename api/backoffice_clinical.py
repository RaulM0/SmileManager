"""Audited, read-only global views for explicitly authorized system administrators."""
import uuid
from django.db.models import Exists, F, OuterRef, Q
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from rest_framework import serializers
from rest_framework.permissions import BasePermission
from rest_framework.response import Response

from Citas.models import Cita
from DiagnosticosIA.models import AIAnalysisRun
from Pacientes.models import (Paciente, AntescedentesMedicos, Consulta, Odontograma,
                              ImagenesClinicas, EstudioComparativo, Consentimiento, ClinicalRevision)
from Usuarios.models import AuditEvent
from .backoffice import AdminAPIView, Pagination


class NoGlobalClinicalAccess(BasePermission):
    """There is no approved tenant-scoped exceptional-access workflow yet."""
    message = 'La consulta clínica global está deshabilitada.'

    def has_permission(self, request, view):
        AuditEvent.objects.create(actor=request.user, action='BACKOFFICE_CLINICAL_ACCESS_DENIED',
                                  resource_type='clinical_access', outcome='failure',
                                  request_id=getattr(request._request, 'request_id', uuid.uuid4()))
        return False


class ClinicalAdminAPIView(AdminAPIView):
    permission_classes = [*AdminAPIView.permission_classes, NoGlobalClinicalAccess]


def audit_read(request, action, resource_type, resource_id=''):
    AuditEvent.objects.create(actor=request.user, action=action, resource_type=resource_type,
                              resource_id=str(resource_id), request_id=request._request.request_id)


def page(request, rows):
    paginator = Pagination()
    return paginator, paginator.paginate_queryset(rows, request)


def patient_rows():
    return Paciente.objects.select_related('medico').only(
        'id', 'nombre', 'appat', 'apmat', 'estatus', 'medico_id', 'medico__username', 'created')


class PatientList(ClinicalAdminAPIView):
    def get(self, request):
        qs = patient_rows().order_by('nombre', 'appat', 'pk')
        search = request.query_params.get('search', '').strip()[:150]
        if search:
            qs = qs.filter(Q(nombre__icontains=search) | Q(appat__icontains=search) | Q(apmat__icontains=search))
        if request.query_params.get('doctor'):
            doctor = serializers.IntegerField(min_value=1).run_validation(request.query_params['doctor'])
            qs = qs.filter(medico_id=doctor)
        state = request.query_params.get('state', '')
        if state not in ('', 'A', 'I'):
            raise serializers.ValidationError({'state': 'Estado no válido.'})
        if state:
            qs = qs.filter(estatus=state)
        paginator, rows = page(request, qs)
        data = [patient_data(item) for item in rows]
        audit_read(request, 'BACKOFFICE_PATIENT_LIST_VIEW', 'patient')
        return paginator.get_paginated_response(data)


def patient_data(patient):
    return {'id': patient.pk, 'nombre': patient.nombre, 'appat': patient.appat,
            'apmat': patient.apmat, 'estatus': patient.estatus, 'created': patient.created,
            'medico_id': patient.medico_id, 'medico': patient.medico.username if patient.medico_id else None}


class PatientDetail(ClinicalAdminAPIView):
    def get(self, request, pk):
        patient = get_object_or_404(patient_rows(), pk=pk)
        data = patient_data(patient)
        data['appointments_count'] = Cita.objects.filter(paciente_id=pk).count()
        data['consultations_count'] = Consulta.objects.filter(paciente_id=pk, medico_id=F('paciente__medico_id')).count()
        data['images_count'] = ImagenesClinicas.objects.filter(paciente_id=pk, medico_id=F('paciente__medico_id')).filter(Q(consulta__isnull=True) | Q(consulta__paciente_id=F('paciente_id'), consulta__medico_id=F('medico_id'))).count()
        audit_read(request, 'BACKOFFICE_PATIENT_VIEW', 'patient', pk)
        return Response(data)


class AppointmentList(ClinicalAdminAPIView):
    def get(self, request):
        qs = appointment_rows().order_by('-fecha', '-hora', '-pk')
        for param, field in (('patient', 'paciente_id'), ('doctor', 'paciente__medico_id')):
            if request.query_params.get(param):
                qs = qs.filter(**{field: serializers.IntegerField(min_value=1).run_validation(request.query_params[param])})
        for param, field in (('from', 'fecha__gte'), ('to', 'fecha__lte')):
            if request.query_params.get(param):
                qs = qs.filter(**{field: serializers.DateField().run_validation(request.query_params[param])})
        state = request.query_params.get('state', '')
        if state not in ('', 'P', 'C', 'A'):
            raise serializers.ValidationError({'state': 'Estado no válido.'})
        if state:
            qs = qs.filter(estatus=state)
        paginator, rows = page(request, qs)
        data = [{'id': row.pk, 'patient_id': row.paciente_id, 'patient': f'{row.paciente.nombre} {row.paciente.appat}',
                 'doctor': row.paciente.medico.username if row.paciente.medico_id else None,
                 'fecha': row.fecha, 'hora': row.hora, 'estatus': row.estatus} for row in rows]
        audit_read(request, 'BACKOFFICE_APPOINTMENTS_VIEW', 'appointment')
        return paginator.get_paginated_response(data)


def appointment_rows():
    return Cita.objects.select_related('paciente', 'paciente__medico').only(
        'id', 'fecha', 'hora', 'estatus', 'paciente_id', 'paciente__nombre',
        'paciente__appat', 'paciente__medico_id', 'paciente__medico__username')


class AppointmentDetail(ClinicalAdminAPIView):
    def get(self, request, pk):
        item = get_object_or_404(appointment_rows(), pk=pk)
        audit_read(request, 'BACKOFFICE_APPOINTMENT_VIEW', 'appointment', pk)
        return Response({'id': item.pk, 'patient_id': item.paciente_id,
                         'patient': f'{item.paciente.nombre} {item.paciente.appat}',
                         'doctor': item.paciente.medico.username if item.paciente.medico_id else None,
                         'fecha': item.fecha, 'hora': item.hora, 'estatus': item.estatus})


SECTIONS = {
    'history': (AntescedentesMedicos, ('id', 'version', 'updated', 'tratamiento_medico', 'problemas_cardiacos', 'problemas_coagulacion', 'epilepsia', 'gastritis', 'hipertension', 'anemia', 'embarazo', 'alergia_medicamentos', 'alergia_especifica', 'discapacidad', 'fuma', 'respiracion_bucal', 'morder_unas', 'chupar_dedo', 'rechinar_dientes', 'sobremordida_vertical', 'sobremordida_horizontal', 'mordida_cruzada', 'mordida_abierta', 'desgaste', 'problemas_atm', 'consumo_citricos', 'sangrado_encias', 'alergias', 'medicamentos', 'cirugias_previas', 'otros'), '-updated'),
    'odontogram': (Odontograma, ('id', 'version', 'updated', 'dientes_permanentes', 'dientes_deciduos', 'resumen_clinico'), '-updated'),
    'consultations': (Consulta, ('id', 'fecha_consulta', 'motivo_consulta', 'diagnostico', 'tratamiento', 'observaciones'), '-fecha_consulta'),
    'images': (ImagenesClinicas, ('id', 'tipo_imagen', 'fecha_subida'), '-fecha_subida'),
    'studies': (EstudioComparativo, ('id', 'fecha_inicio', 'fecha_creacion'), '-fecha_creacion'),
    'consents': (Consentimiento, ('id', 'fecha_aceptacion'), '-id'),
}


class PatientSection(ClinicalAdminAPIView):
    def get(self, request, pk, section):
        get_object_or_404(Paciente.objects.only('pk'), pk=pk)
        if section in SECTIONS:
            model, fields, order = SECTIONS[section]
            rows = model.objects.filter(paciente_id=pk, medico_id=F('paciente__medico_id'))
            if section == 'images':
                rows = rows.filter(Q(consulta__isnull=True) | Q(consulta__paciente_id=F('paciente_id'), consulta__medico_id=F('medico_id')))
            rows = rows.order_by(order, '-pk').values(*fields)
        elif section == 'revisions':
            history = AntescedentesMedicos.objects.filter(pk=OuterRef('resource_id'), paciente_id=pk, medico_id=F('paciente__medico_id'))
            odontogram = Odontograma.objects.filter(pk=OuterRef('resource_id'), paciente_id=pk, medico_id=F('paciente__medico_id'))
            rows = ClinicalRevision.objects.filter(patient_id=pk).annotate(valid_history=Exists(history), valid_odontogram=Exists(odontogram)).filter(Q(resource_type='medical_history', valid_history=True) | Q(resource_type='odontogram', valid_odontogram=True)).order_by('-created', '-pk').values('id', 'resource_type', 'resource_id', 'version', 'created', 'actor_id', 'snapshot')
        elif section == 'ai':
            rows = AIAnalysisRun.objects.filter(image__paciente_id=pk, image__medico_id=F('image__paciente__medico_id')).filter(Q(image__consulta__isnull=True) | Q(image__consulta__paciente_id=F('image__paciente_id'), image__consulta__medico_id=F('image__medico_id'))).order_by('-requested_at', '-pk').values('id', 'status', 'requested_at', 'completed_at', 'model_name', 'model_version', 'failure_category', 'request_id')
        elif section == 'audit':
            rows = AuditEvent.objects.filter(resource_type='patient', resource_id=str(pk)).order_by('-timestamp', '-pk').values('id', 'timestamp', 'actor_id', 'action', 'outcome', 'request_id')
        else:
            from django.http import Http404
            raise Http404
        paginator, result = page(request, rows)
        result = list(result)
        audit_read(request, 'BACKOFFICE_CLINICAL_SECTION_VIEW', 'patient', pk)
        return paginator.get_paginated_response(result)

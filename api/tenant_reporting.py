"""Tenant dashboards and bounded clinical exports."""
from django.conf import settings
from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from Citas.models import Cita
from DiagnosticosIA.models import AIAnalysisRun
from Pacientes.models import Consulta, ImagenesClinicas, Paciente
from Usuarios.models import AuditEvent, ClinicMembership
from .policies import clinic_clinical_queryset
from .serializers import DashboardAppointmentSerializer
from .services.exports import excel_response
from .tenant_context import lock_clinic_capability, require_clinic_capability
from .tenant_patients import TenantClinicalContextMixin
from .throttles import ExportThrottle


@method_decorator(never_cache, name='dispatch')
class TenantDoctorDashboard(TenantClinicalContextMixin, APIView):
    def get(self, request):
        clinic_id = self.membership.clinic_id
        today = timezone.localdate()
        appointments = clinic_clinical_queryset(request.user, clinic_id, Cita).select_related('paciente')
        current = appointments.filter(fecha=today).order_by('hora', 'pk')
        upcoming = appointments.filter(fecha__gt=today).order_by('fecha', 'hora', 'pk')
        limit = settings.DASHBOARD_APPOINTMENT_LIMIT
        data = {'patient_count': clinic_clinical_queryset(request.user, clinic_id, Paciente).count(),
                'today_count': current.count(),
                'today': DashboardAppointmentSerializer(current[:limit], many=True).data,
                'upcoming': DashboardAppointmentSerializer(upcoming[:limit], many=True).data}
        AuditEvent.objects.create(actor=request.user, clinic_id=clinic_id, action='TENANT_DOCTOR_DASHBOARD_VIEWED',
                                  resource_type='dashboard', request_id=request._request.request_id)
        return Response(data)


@method_decorator(never_cache, name='dispatch')
class TenantAdminDashboard(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def get(self, request):
        membership = require_clinic_capability(request.user, request.headers.get('X-Clinic-ID'), 'clinic.manage')
        membership = lock_clinic_capability(request.user, membership.clinic_id, 'clinic.manage')
        clinic_id = membership.clinic_id
        today = timezone.localdate()
        patients = Paciente.objects.filter(clinic_id=clinic_id).aggregate(active=Count('id', filter=Q(estatus='A')))
        appointments = Cita.objects.filter(paciente__clinic_id=clinic_id).aggregate(
            today=Count('id', filter=Q(fecha=today)), pending=Count('id', filter=Q(estatus='P')))
        members = ClinicMembership.objects.filter(clinic_id=clinic_id, status='ACTIVE', user__is_active=True).aggregate(
            doctors=Count('id', filter=Q(role='DOCTOR')), staff=Count('id', filter=Q(role='STAFF')))
        runs = AIAnalysisRun.objects.filter(clinic_id=clinic_id, image__paciente__clinic_id=clinic_id).aggregate(
            total=Count('id'), failed=Count('id', filter=Q(status='FAILED')))
        AuditEvent.objects.create(actor=request.user, clinic_id=clinic_id, action='TENANT_ADMIN_DASHBOARD_VIEWED',
                                  resource_type='dashboard', request_id=request._request.request_id)
        return Response({'patients': patients, 'appointments': appointments, 'members': members, 'ai': runs})


@method_decorator(never_cache, name='dispatch')
class TenantClinicalExport(TenantClinicalContextMixin, APIView):
    throttle_classes = [ExportThrottle]

    def get(self, request, kind):
        if kind == 'patients':
            rows = clinic_clinical_queryset(request.user, self.membership.clinic_id, Paciente).values(
                'id', 'nombre', 'appat', 'apmat', 'fecha_nacimiento', 'genero', 'telefono', 'email', 'estatus')
            filename, sheet = 'Pacientes.xlsx', 'Pacientes'
        elif kind == 'consultations':
            rows = clinic_clinical_queryset(request.user, self.membership.clinic_id, Consulta).values(
                'paciente__nombre', 'paciente__appat', 'paciente__apmat', 'fecha_consulta',
                'motivo_consulta', 'diagnostico', 'tratamiento', 'observaciones')
            filename, sheet = 'Consultas.xlsx', 'Consultas'
        elif kind == 'clinical-images':
            rows = clinic_clinical_queryset(request.user, self.membership.clinic_id, ImagenesClinicas).values(
                'paciente_id', 'consulta_id', 'tipo_imagen', 'descripcion', 'fecha_subida')
            filename, sheet = 'ImagenesClinicas.xlsx', 'ImagenesClinicas'
        else:
            return Response({'detail': 'Exportación no disponible.'}, status=404)
        response = excel_response(rows, filename=filename, sheet=sheet)
        if response.status_code == 200:
            AuditEvent.objects.create(actor=request.user, clinic_id=self.membership.clinic_id,
                                      action='TENANT_CLINICAL_EXPORT', resource_type=kind,
                                      request_id=request._request.request_id)
        response['Cache-Control'] = 'private, no-store'
        return response

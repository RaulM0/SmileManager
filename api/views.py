import logging
import os
import uuid

from django.contrib.auth import authenticate, get_user_model
from django.conf import settings
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from urllib.parse import urlsplit
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.http import FileResponse
from django.db.models import Q, Value
from django.db.models.functions import Concat
from rest_framework import permissions, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from Citas.models import Cita
from Pacientes.models import AntescedentesMedicos, Consentimiento, Consulta, EstudioComparativo, ImagenesClinicas, Odontograma, Paciente
from Pacientes.PDF import pdf_progreso
from DiagnosticosIA.services import ClinicalImageMissingError, analyze_clinical_image
from DiagnosticosIA.services import ClinicalImageChangedError
from DiagnosticosIA.runs import execute as execute_analysis
from DiagnosticosIA.runs import AnalysisKeyConflict
from DiagnosticosIA.models import AIAnalysisRun
from django.core.files.storage import default_storage

from .serializers import (
    ConsultationSerializer,
    AppointmentSerializer,
    ClinicalImageSerializer,
    ComparativeStudySerializer,
    ConsentSerializer,
    DashboardAppointmentSerializer,
    MedicalHistorySerializer,
    OdontogramSerializer,
    PatientSerializer,
    SessionUserSerializer,
)
from .services.patients import deactivate_patient
from .services.exports import export_consultations, export_images, export_patients
from .services.emails import send_patient_email
from .services.appointments import transition_appointment
from .services.clinical_records import save_record
from .policies import scoped, owned_or_404, consistent_or_404
from .upload_policy import validate_upload
from django.core.exceptions import ValidationError as DjangoValidationError
from .throttles import AddressThrottle, AccountThrottle, ExpensiveThrottle, EmailThrottle, ExportThrottle

logger=logging.getLogger(__name__)


class LoginInputSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=100)
    password = serializers.CharField(trim_whitespace=False, write_only=True)


REFRESH_COOKIE = 'smile_refresh'
REFRESH_COOKIE_PATH = '/api/v1/auth/'


def _auth_origin_allowed(request):
    origin = request.headers.get('Origin')
    if not origin:
        return True
    parsed = urlsplit(origin)
    own_origin = f'{request.scheme}://{request.get_host()}'
    return origin == own_origin or origin in settings.CSRF_TRUSTED_ORIGINS


def _refresh_user(request):
    raw = request.COOKIES.get(REFRESH_COOKIE)
    if not raw:
        return None, None
    try:
        token = RefreshToken(raw)
        user = get_user_model().objects.get(pk=token['user_id'], is_active=True)
        return token, user
    except (TokenError, KeyError, ValueError, get_user_model().DoesNotExist):
        return None, None


def _set_refresh_cookie(response, token):
    response.set_cookie(
        REFRESH_COOKIE, str(token), path=REFRESH_COOKIE_PATH,
        secure=settings.SESSION_COOKIE_SECURE, httponly=True, samesite='Strict',
    )
    response['Cache-Control'] = 'no-store'
    return response


@method_decorator(never_cache, name='dispatch')
class SessionView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    throttle_classes = [AddressThrottle]

    def get(self, request):
        token, user = _refresh_user(request)
        if user is None:
            return Response({'authenticated': False})
        return Response({
            'authenticated': True,
            'access': str(token.access_token),
            'user': SessionUserSerializer(user).data,
        })


@method_decorator(never_cache, name='dispatch')
class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    throttle_classes = [AddressThrottle, AccountThrottle]

    def post(self, request):
        if not _auth_origin_allowed(request):
            return Response({'detail': 'Origen no permitido.'}, status=status.HTTP_403_FORBIDDEN)
        serializer = LoginInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(
            request,
            username=serializer.validated_data['username'],
            password=serializer.validated_data['password'],
        )
        if user is None:
            request._request.audit_auth_event = ('AUTH_LOGIN_FAILED', None, 'failure')
            return Response(
                {'detail': 'Usuario o contraseña incorrectos'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        request._request.audit_auth_event = ('AUTH_LOGIN_SUCCESS', user, 'success')
        refresh = RefreshToken.for_user(user)
        response = Response({
            'authenticated': True,
            'access': str(refresh.access_token),
            'user': SessionUserSerializer(user).data,
        })
        return _set_refresh_cookie(response, refresh)


@method_decorator(never_cache, name='dispatch')
class RefreshView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    throttle_classes = [AddressThrottle]

    def post(self, request):
        if not _auth_origin_allowed(request):
            return Response({'detail': 'Origen no permitido.'}, status=status.HTTP_403_FORBIDDEN)
        token, user = _refresh_user(request)
        if user is None:
            response = Response({'detail': 'Sesión expirada.'}, status=status.HTTP_401_UNAUTHORIZED)
            response.delete_cookie(REFRESH_COOKIE, path=REFRESH_COOKIE_PATH)
            return response
        try:
            with transaction.atomic():
                OutstandingToken.objects.select_for_update().get(jti=token['jti'])
                token = RefreshToken(request.COOKIES[REFRESH_COOKIE])
                token.blacklist()
                rotated = RefreshToken.for_user(user)
        except (TokenError, OutstandingToken.DoesNotExist):
            response = Response({'detail': 'Sesión expirada.'}, status=status.HTTP_401_UNAUTHORIZED)
            response.delete_cookie(REFRESH_COOKIE, path=REFRESH_COOKIE_PATH)
            return response
        return _set_refresh_cookie(Response({'access': str(rotated.access_token)}), rotated)


@method_decorator(never_cache, name='dispatch')
class LogoutView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        if not _auth_origin_allowed(request):
            return Response({'detail': 'Origen no permitido.'}, status=status.HTTP_403_FORBIDDEN)
        token, user = _refresh_user(request)
        if token:
            try:
                with transaction.atomic():
                    OutstandingToken.objects.select_for_update().get(jti=token['jti'])
                    RefreshToken(request.COOKIES[REFRESH_COOKIE]).blacklist()
                    request._request.audit_auth_event = ('AUTH_LOGOUT', user, 'success')
            except (TokenError, OutstandingToken.DoesNotExist):
                pass
        response = Response(status=status.HTTP_204_NO_CONTENT)
        response.delete_cookie(REFRESH_COOKIE, path=REFRESH_COOKIE_PATH)
        response['Cache-Control'] = 'no-store'
        return response


class DashboardView(APIView):
    def get(self, request):
        today = timezone.localdate()
        appointments = scoped(request.user, Cita).select_related('paciente')
        todays = appointments.filter(fecha=today).order_by('hora', 'pk')
        upcoming = appointments.filter(fecha__gt=today).order_by('fecha', 'hora', 'pk')
        limit = settings.DASHBOARD_APPOINTMENT_LIMIT
        return Response({
            'patient_count': scoped(request.user, Paciente).count(),
            'today_count': todays.count(),
            'today': DashboardAppointmentSerializer(todays[:limit], many=True).data,
            'upcoming': DashboardAppointmentSerializer(upcoming[:limit], many=True).data,
        })


class PatientPagination(PageNumberPagination):
    page_size = 10


class ClinicalPagination(PageNumberPagination):
    page_size_query_param = 'page_size'

    def get_page_size(self, request):
        self.page_size = settings.CLINICAL_PAGE_SIZE
        self.max_page_size = settings.CLINICAL_MAX_PAGE_SIZE
        return super().get_page_size(request)


class PatientViewSet(viewsets.ModelViewSet):
    serializer_class = PatientSerializer
    pagination_class = PatientPagination
    http_method_names = ['get', 'post', 'patch', 'put', 'head', 'options']

    def get_queryset(self):
        queryset = scoped(self.request.user, Paciente).order_by('appat')
        search = self.request.query_params.get('search', '').strip()
        if search:
            queryset = queryset.annotate(
                full_name=Concat('nombre', Value(' '), 'appat', Value(' '), 'apmat')
            ).filter(
                Q(nombre__icontains=search)
                | Q(appat__icontains=search)
                | Q(apmat__icontains=search)
                | Q(telefono__icontains=search)
                | Q(email__icontains=search)
                | Q(full_name__icontains=search)
            )
        return queryset

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        patient = deactivate_patient(self.get_object())
        return Response(self.get_serializer(patient).data)

    @action(detail=False, methods=['get'], pagination_class=None)
    def autocomplete(self, request):
        term = request.query_params.get('term', '').strip()
        patients = self.get_queryset().annotate(
            full_name=Concat('nombre', Value(' '), 'appat', Value(' '), 'apmat')
        )
        query = Q(nombre__icontains=term) | Q(appat__icontains=term) | Q(apmat__icontains=term) | Q(full_name__icontains=term) | Q(telefono__icontains=term)
        if term.isdigit():
            query |= Q(id=int(term))
        patients = patients.filter(query)[:10]
        return Response({
            'results': [
                {'id': patient.id, 'text': f'{patient.nombre} {patient.appat} {patient.apmat}'}
                for patient in patients
            ]
        })


class OwnedPatientMixin:
    def patient(self, request, patient_id):
        return owned_or_404(request.user, Paciente, pk=patient_id)


class MedicalHistoryView(OwnedPatientMixin, APIView):
    def get(self, request, patient_id):
        patient = self.patient(request, patient_id)
        history = consistent_or_404(request.user, AntescedentesMedicos, patient).first()
        if history is None:
            history = AntescedentesMedicos(paciente=patient, medico=request.user)
        return Response(MedicalHistorySerializer(history).data)

    def put(self, request, patient_id):
        patient = self.patient(request, patient_id)
        history = consistent_or_404(request.user, AntescedentesMedicos, patient).first() or AntescedentesMedicos(paciente=patient, medico=request.user)
        serializer = MedicalHistorySerializer(history, data=request.data)
        serializer.is_valid(raise_exception=True)
        history = save_record(user=request.user, patient_id=patient_id, model=AntescedentesMedicos, changes=serializer.validated_data, expected_version=request.data.get('version'))
        return Response(MedicalHistorySerializer(history).data)


class ConsultationListCreateView(OwnedPatientMixin, APIView):
    def get(self, request, patient_id):
        patient = self.patient(request, patient_id)
        consultations = scoped(request.user, Consulta).filter(paciente=patient).select_related('paciente').order_by('-fecha_consulta', '-pk')
        paginator = ClinicalPagination()
        page = paginator.paginate_queryset(consultations, request, view=self)
        return paginator.get_paginated_response(ConsultationSerializer(page, many=True).data)

    def post(self, request, patient_id):
        patient = self.patient(request, patient_id)
        serializer = ConsultationSerializer(
            data=request.data,
            context={'request': request, 'patient': patient},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ConsultationDetailView(APIView):
    def get(self, request, consultation_id):
        consultation = get_object_or_404(
            scoped(request.user, Consulta).select_related('paciente'),
            pk=consultation_id,
            medico=request.user,
        )
        return Response(ConsultationSerializer(consultation).data)


class AppointmentViewSet(viewsets.ModelViewSet):
    serializer_class = AppointmentSerializer
    pagination_class = ClinicalPagination
    http_method_names = ['get', 'post', 'patch', 'put', 'head', 'options']

    def get_queryset(self):
        queryset = scoped(self.request.user, Cita).select_related('paciente').order_by('fecha', 'hora', 'pk')
        start = self.request.query_params.get('from')
        end = self.request.query_params.get('to')
        if start or end:
            try:
                start_date = parse_date(start or '')
                end_date = parse_date(end or '')
            except ValueError:
                start_date = end_date = None
            if not start_date or not end_date or start_date > end_date or (end_date - start_date).days + 1 > settings.APPOINTMENT_MAX_RANGE_DAYS:
                raise serializers.ValidationError({'detail': 'Indica un rango de fechas válido dentro del límite permitido.'})
            queryset = queryset.filter(fecha__range=(start_date, end_date))
        appointment_status = self.request.query_params.get('status')
        if appointment_status:
            queryset = queryset.filter(estatus=appointment_status)
        search = self.request.query_params.get('search', '').strip()
        if search:
            query = (
                Q(paciente__nombre__icontains=search)
                | Q(paciente__appat__icontains=search)
                | Q(paciente__telefono__icontains=search)
            )
            if search.isdigit():
                query |= Q(id=int(search))
            queryset = queryset.filter(query)
        return queryset

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        appointment = self.get_object()
        appointment = transition_appointment(user=request.user, appointment=appointment, target='C')
        return Response(self.get_serializer(appointment).data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        appointment = self.get_object()
        appointment = transition_appointment(user=request.user, appointment=appointment, target='A')
        return Response(self.get_serializer(appointment).data)


class ClinicalImageListCreateView(OwnedPatientMixin, APIView):
    def get(self, request, patient_id):
        patient = self.patient(request, patient_id)
        images = scoped(request.user, ImagenesClinicas).filter(paciente=patient).select_related('consulta', 'paciente').order_by('-fecha_subida', '-pk')
        date_filter = request.query_params.get('date')
        consultation_id = request.query_params.get('consultation_id')
        if date_filter:
            images = images.filter(fecha_subida__date=date_filter)
        if consultation_id and consultation_id.isdigit():
            images = images.filter(
                consulta_id=consultation_id,
                consulta__medico=request.user,
            )
        paginator = ClinicalPagination()
        page = paginator.paginate_queryset(images, request, view=self)
        return paginator.get_paginated_response(ClinicalImageSerializer(page, many=True).data)

    def post(self, request, patient_id):
        patient = self.patient(request, patient_id)
        serializer = ClinicalImageSerializer(
            data=request.data,
            context={'request': request, 'patient': patient},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@method_decorator(never_cache, name='dispatch')
class ClinicalImageViewSet(viewsets.GenericViewSet):
    serializer_class = ClinicalImageSerializer

    def get_queryset(self):
        return scoped(self.request.user, ImagenesClinicas).select_related('paciente', 'consulta')

    def retrieve(self, request, pk=None):
        return Response(self.get_serializer(self.get_object()).data)

    def destroy(self, request, pk=None):
        self.get_object().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'], url_path='file')
    def file(self, request, pk=None):
        image = self.get_object()
        if not image.imagen:
            return Response({'detail': 'La imagen original no está disponible. Recupera el archivo original o vuelve a cargarlo en el expediente.', 'code': 'source_image_missing'}, status=status.HTTP_404_NOT_FOUND)
        try:
            return FileResponse(image.imagen.open('rb'), as_attachment=True, filename=os.path.basename(image.imagen.name))
        except FileNotFoundError:
            return Response({'detail': 'La imagen original no está disponible. Recupera el archivo original o vuelve a cargarlo en el expediente.', 'code': 'source_image_missing'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['get'], url_path='result-file')
    def result_file(self, request, pk=None):
        image = self.get_object()
        if not image.resultados:
            return Response({'detail': 'La imagen analizada no está disponible.'}, status=status.HTTP_404_NOT_FOUND)
        try:
            return FileResponse(image.resultados.open('rb'), as_attachment=True, filename=os.path.basename(image.resultados.name))
        except FileNotFoundError:
            return Response({'detail': 'La imagen analizada no está disponible.'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'], throttle_classes=[ExpensiveThrottle])
    def analyze(self, request, pk=None):
        image=self.get_object()
        force = request.data.get('force', False)
        if not isinstance(force, bool):
            return Response({'detail': 'force debe ser booleano.'}, status=400)
        raw_key = request.headers.get('Idempotency-Key')
        try:
            key = uuid.UUID(raw_key) if raw_key else None
        except ValueError:
            return Response({'detail': 'Idempotency-Key inválida.'}, status=400)
        try: run, result = execute_analysis(user=request.user, image_id=image.pk, request_id=request._request.request_id, force=force, analyzer=analyze_clinical_image, idempotency_key=key if force else None)
        except ClinicalImageMissingError:
            logger.warning('La imagen original de la imagen clínica %s no existe en el almacenamiento', image.pk)
            return Response({'detail': 'La imagen original no está disponible. Recupera el archivo original o vuelve a cargarlo en el expediente.', 'code': 'source_image_missing'}, status=status.HTTP_404_NOT_FOUND)
        except ClinicalImageChangedError:
            return Response({'detail': 'La imagen cambió durante el análisis. Vuelve a intentarlo.'}, status=409)
        except AnalysisKeyConflict:
            return Response({'detail': 'La clave ya corresponde a otro análisis.'}, status=409)
        except Exception:
            logger.error('Fallo de análisis de imagen clínica id=%s request_id=%s', image.pk, request._request.request_id)
            return Response({'detail':'No se pudo analizar la imagen. Inténtalo de nuevo.'},status=500)
        image.refresh_from_db()
        if run.status == AIAnalysisRun.FAILED:
            return Response({'detail': 'La ejecución anterior falló. Solicita un nuevo análisis.', 'run_id': run.pk}, status=409)
        if result == 'reused' and (not run.result_name or image.resultados.name != run.result_name or not default_storage.exists(run.result_name)):
            return Response({'detail': 'El resultado de esa ejecución no está disponible como resultado actual.', 'run_id': run.pk}, status=409)
        return Response({'image':self.get_serializer(image).data,'detections':run.detections,'run_id':run.pk,'status':run.status,'disposition':result}, status=202 if result == 'running' else 200)

    @action(detail=True, methods=['get'], url_path='analysis-runs')
    def analysis_runs(self, request, pk=None):
        image = self.get_object()
        runs = image.analysis_runs.order_by('-requested_at', '-pk')
        paginator = ClinicalPagination()
        page = paginator.paginate_queryset(runs, request, view=self)
        return paginator.get_paginated_response([{'id': r.pk, 'status': r.status, 'requested_by': r.requested_by_id, 'requested_at': r.requested_at, 'started_at': r.started_at, 'completed_at': r.completed_at, 'model_name': r.model_name, 'model_version': r.model_version, 'explicit_reanalysis': r.explicit_reanalysis, 'failure_category': r.failure_category, 'has_result': bool(r.result_name)} for r in page])


@method_decorator(never_cache, name='dispatch')
class AnalysisRunFileView(APIView):
    def get(self, request, image_id, run_id):
        image = owned_or_404(request.user, ImagenesClinicas, pk=image_id)
        run = get_object_or_404(AIAnalysisRun, image=image, pk=run_id, status=AIAnalysisRun.SUCCEEDED)
        if not run.result_name:
            return Response({'detail': 'Resultado no disponible.'}, status=404)
        try:
            return FileResponse(default_storage.open(run.result_name, 'rb'), as_attachment=True, filename=os.path.basename(run.result_name))
        except FileNotFoundError:
            return Response({'detail': 'Resultado no disponible.'}, status=404)


class OdontogramView(OwnedPatientMixin, APIView):
    def get(self, request, patient_id):
        patient = self.patient(request, patient_id)
        odontogram = consistent_or_404(request.user, Odontograma, patient).order_by('-created').first()
        if odontogram is None:
            return Response({
                'id': None,
                'denticion_permanente': {},
                'denticion_decidua': {},
                'resumen': {},
                'created': None,
                'updated': None,
                'version': 0,
            })
        return Response(OdontogramSerializer(odontogram).data)

    def put(self, request, patient_id):
        patient = self.patient(request, patient_id)
        odontogram = consistent_or_404(request.user, Odontograma, patient).first() or Odontograma(paciente=patient, medico=request.user)
        serializer = OdontogramSerializer(odontogram, data=request.data)
        serializer.is_valid(raise_exception=True)
        odontogram = save_record(user=request.user, patient_id=patient_id, model=Odontograma, changes=serializer.validated_data, expected_version=request.data.get('version'))
        return Response(OdontogramSerializer(odontogram).data)


class ComparativeStudyView(OwnedPatientMixin, APIView):
    def get_object(self, request, patient_id):
        patient=self.patient(request,patient_id)
        return patient, consistent_or_404(request.user, EstudioComparativo, patient).order_by('-fecha_creacion').first()
    def get(self,request,patient_id):
        _,study=self.get_object(request,patient_id)
        return Response({'exists':False} if study is None else {'exists':True,**ComparativeStudySerializer(study).data})
    def put(self,request,patient_id):
        patient,study=self.get_object(request,patient_id)
        serializer=ComparativeStudySerializer(study,data=request.data,partial=study is not None); serializer.is_valid(raise_exception=True); serializer.save(paciente=patient,medico=request.user)
        return Response({'exists':True,**serializer.data})

class ComparativeStudyPdfView(OwnedPatientMixin, APIView):
    def get(self,request,patient_id): self.patient(request,patient_id); return pdf_progreso(request,patient_id)


@method_decorator(never_cache, name='dispatch')
class ComparativeStudyImageView(OwnedPatientMixin, APIView):
    allowed_fields = ('antes_oclusal_superior', 'antes_lateral_izquierda', 'antes_frontal', 'antes_lateral_derecha', 'antes_oclusal_inferior', 'despues_perfil', 'despues_semiperfil', 'despues_retrato_frontal', 'despues_retrato_sonrisa')

    def get(self, request, patient_id, field):
        patient = self.patient(request, patient_id)
        if field not in self.allowed_fields:
            return Response({'detail': 'Imagen no encontrada.'}, status=status.HTTP_404_NOT_FOUND)
        study = consistent_or_404(request.user, EstudioComparativo, patient).order_by('-fecha_creacion').first()
        file = getattr(study, field, None) if study else None
        if not file:
            return Response({'detail': 'Imagen no encontrada.'}, status=status.HTTP_404_NOT_FOUND)
        return FileResponse(file.open('rb'), filename=os.path.basename(file.name))

class ConsentView(OwnedPatientMixin, APIView):
    allowed_extensions={'.jpg','.jpeg','.png','.gif','.pdf'}
    def get_object(self,request,patient_id):
        patient=self.patient(request,patient_id)
        return consistent_or_404(request.user, Consentimiento, patient).first() or Consentimiento(paciente=patient,medico=request.user,texto='')
    def get(self,request,patient_id): return Response(ConsentSerializer(self.get_object(request,patient_id)).data)
    def post(self,request,patient_id):
        consent=self.get_object(request,patient_id)
        if consent.fecha_aceptacion: return Response({'detail':'El consentimiento ya fue aceptado.'},status=status.HTTP_409_CONFLICT)
        uploaded=request.FILES.get('archivo_ine')
        if uploaded is None: return Response({'archivo_ine':['Este archivo es obligatorio.']},status=400)
        try: validate_upload(uploaded, allow_pdf=True)
        except DjangoValidationError as exc: return Response({'archivo_ine':exc.messages},status=400)
        consent.texto=request.data.get('texto',''); consent.archivo_ine=uploaded; consent.fecha_aceptacion=timezone.now(); consent.save()
        return Response(ConsentSerializer(consent).data)


@method_decorator(never_cache, name='dispatch')
class ConsentFileView(OwnedPatientMixin, APIView):
    def get(self, request, patient_id):
        patient = self.patient(request, patient_id)
        consent = get_object_or_404(consistent_or_404(request.user, Consentimiento, patient))
        if not consent.archivo_ine:
            return Response({'detail': 'Identificación no disponible.'}, status=status.HTTP_404_NOT_FOUND)
        return FileResponse(consent.archivo_ine.open('rb'), as_attachment=True, filename=os.path.basename(consent.archivo_ine.name))

@method_decorator(never_cache, name='dispatch')
class ConsentPdfView(OwnedPatientMixin, APIView):
    def get(self, request, patient_id):
        patient = self.patient(request, patient_id)
        consent = get_object_or_404(consistent_or_404(request.user, Consentimiento, patient))
        if not consent.pdf_generado:
            return Response({'detail': 'Documento no disponible.'}, status=status.HTTP_404_NOT_FOUND)
        return FileResponse(consent.pdf_generado.open('rb'), as_attachment=True, filename=os.path.basename(consent.pdf_generado.name))

class PatientEmailInputSerializer(serializers.Serializer):
    asunto=serializers.CharField()
    mensaje=serializers.CharField()

class PatientEmailView(OwnedPatientMixin, APIView):
    throttle_classes = [EmailThrottle]
    def post(self,request,patient_id):
        patient=self.patient(request,patient_id); serializer=PatientEmailInputSerializer(data=request.data); serializer.is_valid(raise_exception=True)
        send_patient_email(patient=patient,user=request.user,subject=serializer.validated_data['asunto'],message=serializer.validated_data['mensaje'])
        return Response({'detail':f'Correo enviado exitosamente a {patient.email}.'})

class PatientExportView(APIView):
    throttle_classes = [ExportThrottle]
    def get(self,request): return export_patients(request.user)
class ConsultationExportView(APIView):
    throttle_classes = [ExportThrottle]
    def get(self,request): return export_consultations(request.user)
class ClinicalImageExportView(APIView):
    throttle_classes = [ExportThrottle]
    def get(self,request): return export_images(request.user)

class DiagnosticsView(APIView):
    def get(self,request):
        images=scoped(request.user, ImagenesClinicas).select_related('paciente').order_by('-fecha_subida')
        patient=request.query_params.get('patient'); image_type=request.query_params.get('type'); date=request.query_params.get('date')
        if patient: images=images.filter(paciente__nombre__icontains=patient)
        if image_type: images=images.filter(tipo_imagen=image_type)
        if date: images=images.filter(fecha_subida__date=date)
        total=images.count(); processed=images.filter(resultados__isnull=False).exclude(resultados='').count()
        paginator=PatientPagination(); page=paginator.paginate_queryset(images,request)
        response=paginator.get_paginated_response(ClinicalImageSerializer(page,many=True).data)
        response.data['statistics']={'total':total,'processed':processed,'pending':total-processed,'processed_percentage':round(processed/total*100,2) if total else 0,'type_count':images.values('tipo_imagen').distinct().count()}
        return response

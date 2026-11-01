import logging
import os

from django.contrib.auth import authenticate, login, logout
from django.middleware.csrf import get_token
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.shortcuts import get_object_or_404
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
from DiagnosticosIA.services import analyze_clinical_image

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

logger=logging.getLogger(__name__)


class LoginInputSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=100)
    password = serializers.CharField(trim_whitespace=False, write_only=True)


@method_decorator(ensure_csrf_cookie, name='dispatch')
class SessionView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        csrf_token = get_token(request)
        if not request.user.is_authenticated:
            return Response({'authenticated': False, 'csrf_token': csrf_token})
        return Response({
            'authenticated': True,
            'csrf_token': csrf_token,
            'user': SessionUserSerializer(request.user).data,
        })


@method_decorator(csrf_protect, name='dispatch')
class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = LoginInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(
            request,
            username=serializer.validated_data['username'],
            password=serializer.validated_data['password'],
        )
        if user is None:
            return Response(
                {'detail': 'Usuario o contraseña incorrectos'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        login(request, user)
        return Response({
            'authenticated': True,
            'csrf_token': get_token(request),
            'user': SessionUserSerializer(user).data,
        })


class LogoutView(APIView):
    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class DashboardView(APIView):
    def get(self, request):
        today = timezone.localdate()
        appointments = Cita.objects.filter(
            paciente__medico=request.user,
        ).select_related('paciente')
        todays = appointments.filter(fecha=today)
        upcoming = appointments.filter(fecha__gt=today)
        return Response({
            'patient_count': Paciente.objects.filter(medico=request.user).count(),
            'today': DashboardAppointmentSerializer(todays, many=True).data,
            'upcoming': DashboardAppointmentSerializer(upcoming, many=True).data,
        })


class PatientPagination(PageNumberPagination):
    page_size = 10


class PatientViewSet(viewsets.ModelViewSet):
    serializer_class = PatientSerializer
    pagination_class = PatientPagination
    http_method_names = ['get', 'post', 'patch', 'put', 'head', 'options']

    def get_queryset(self):
        queryset = Paciente.objects.filter(medico=self.request.user).order_by('appat')
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
        term = request.query_params.get('term', '')
        patients = self.get_queryset().filter(nombre__icontains=term)[:10]
        return Response({
            'results': [
                {'id': patient.id, 'text': f'{patient.nombre} {patient.appat} {patient.apmat}'}
                for patient in patients
            ]
        })


class OwnedPatientMixin:
    def patient(self, request, patient_id):
        return get_object_or_404(Paciente, pk=patient_id, medico=request.user)


class MedicalHistoryView(OwnedPatientMixin, APIView):
    def get_object(self, request, patient_id):
        patient = self.patient(request, patient_id)
        history, _ = AntescedentesMedicos.objects.get_or_create(
            paciente=patient,
            defaults={'medico': request.user},
        )
        return history

    def get(self, request, patient_id):
        return Response(MedicalHistorySerializer(self.get_object(request, patient_id)).data)

    def put(self, request, patient_id):
        history = self.get_object(request, patient_id)
        serializer = MedicalHistorySerializer(history, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(medico=request.user)
        return Response(serializer.data)


class ConsultationListCreateView(OwnedPatientMixin, APIView):
    def get(self, request, patient_id):
        patient = self.patient(request, patient_id)
        consultations = Consulta.objects.filter(
            paciente=patient, medico=request.user,
        ).order_by('-fecha_consulta')
        return Response(ConsultationSerializer(consultations, many=True).data)

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
            Consulta.objects.select_related('paciente'),
            pk=consultation_id,
            medico=request.user,
        )
        return Response(ConsultationSerializer(consultation).data)


class AppointmentViewSet(viewsets.ModelViewSet):
    serializer_class = AppointmentSerializer
    http_method_names = ['get', 'post', 'patch', 'put', 'head', 'options']

    def get_queryset(self):
        queryset = Cita.objects.filter(
            paciente__medico=self.request.user,
        ).select_related('paciente').order_by('fecha', 'hora')
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
        appointment.estatus = 'C'
        appointment.save(update_fields=['estatus', 'updated'])
        return Response(self.get_serializer(appointment).data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        appointment = self.get_object()
        appointment.estatus = 'A'
        appointment.save(update_fields=['estatus', 'updated'])
        return Response(self.get_serializer(appointment).data)


class ClinicalImageListCreateView(OwnedPatientMixin, APIView):
    def get(self, request, patient_id):
        patient = self.patient(request, patient_id)
        images = ImagenesClinicas.objects.filter(
            paciente=patient, medico=request.user,
        ).select_related('consulta').order_by('-fecha_subida')
        date_filter = request.query_params.get('date')
        consultation_id = request.query_params.get('consultation_id')
        if date_filter:
            images = images.filter(fecha_subida__date=date_filter)
        if consultation_id and consultation_id.isdigit():
            images = images.filter(
                consulta_id=consultation_id,
                consulta__medico=request.user,
            )
        return Response(ClinicalImageSerializer(images, many=True).data)

    def post(self, request, patient_id):
        patient = self.patient(request, patient_id)
        serializer = ClinicalImageSerializer(
            data=request.data,
            context={'request': request, 'patient': patient},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ClinicalImageViewSet(viewsets.GenericViewSet):
    serializer_class = ClinicalImageSerializer

    def get_queryset(self):
        return ImagenesClinicas.objects.filter(
            medico=self.request.user,
        ).select_related('paciente', 'consulta')

    def retrieve(self, request, pk=None):
        return Response(self.get_serializer(self.get_object()).data)

    def destroy(self, request, pk=None):
        self.get_object().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def analyze(self, request, pk=None):
        image=self.get_object()
        try: detections=analyze_clinical_image(image)
        except Exception as exc:
            logger.exception('Error al analizar la imagen clínica %s',image.pk)
            return Response({'detail':f'Error al ejecutar YOLO: {exc}'},status=500)
        image.refresh_from_db()
        return Response({'image':self.get_serializer(image).data,'detections':detections})


class OdontogramView(OwnedPatientMixin, APIView):
    def get(self, request, patient_id):
        patient = self.patient(request, patient_id)
        odontogram = patient.odontogramas.filter(medico=request.user).order_by('-created').first()
        if odontogram is None:
            return Response({
                'id': None,
                'denticion_permanente': {},
                'denticion_decidua': {},
                'resumen': {},
                'created': None,
                'updated': None,
            })
        return Response(OdontogramSerializer(odontogram).data)

    def put(self, request, patient_id):
        patient = self.patient(request, patient_id)
        odontogram, _ = Odontograma.objects.get_or_create(
            paciente=patient,
            medico=request.user,
            defaults={
                'dientes_permanentes': {},
                'dientes_deciduos': {},
                'resumen_clinico': {},
            },
        )
        serializer = OdontogramSerializer(odontogram, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class ComparativeStudyView(OwnedPatientMixin, APIView):
    def get_object(self, request, patient_id):
        patient=self.patient(request,patient_id)
        return patient, EstudioComparativo.objects.filter(paciente=patient,medico=request.user).order_by('-fecha_creacion').first()
    def get(self,request,patient_id):
        _,study=self.get_object(request,patient_id)
        return Response({'exists':False} if study is None else {'exists':True,**ComparativeStudySerializer(study).data})
    def put(self,request,patient_id):
        patient,study=self.get_object(request,patient_id)
        serializer=ComparativeStudySerializer(study,data=request.data,partial=study is not None); serializer.is_valid(raise_exception=True); serializer.save(paciente=patient,medico=request.user)
        return Response({'exists':True,**serializer.data})

class ComparativeStudyPdfView(OwnedPatientMixin, APIView):
    def get(self,request,patient_id): self.patient(request,patient_id); return pdf_progreso(request,patient_id)

class ConsentView(OwnedPatientMixin, APIView):
    allowed_extensions={'.jpg','.jpeg','.png','.gif','.pdf'}
    def get_object(self,request,patient_id):
        patient=self.patient(request,patient_id)
        consent,_=Consentimiento.objects.get_or_create(paciente=patient,medico=request.user,defaults={'texto':''})
        return consent
    def get(self,request,patient_id): return Response(ConsentSerializer(self.get_object(request,patient_id)).data)
    def post(self,request,patient_id):
        consent=self.get_object(request,patient_id)
        if consent.fecha_aceptacion: return Response({'detail':'El consentimiento ya fue aceptado.'},status=status.HTTP_409_CONFLICT)
        uploaded=request.FILES.get('archivo_ine')
        if uploaded is None: return Response({'archivo_ine':['Este archivo es obligatorio.']},status=400)
        if uploaded.size>5*1024*1024: return Response({'archivo_ine':['El archivo no debe superar los 5 MB.']},status=400)
        if os.path.splitext(uploaded.name)[1].lower() not in self.allowed_extensions: return Response({'archivo_ine':['Solo se permiten archivos tipo imagen o PDF.']},status=400)
        consent.texto=request.data.get('texto',''); consent.archivo_ine=uploaded; consent.fecha_aceptacion=timezone.now(); consent.save()
        return Response(ConsentSerializer(consent).data)

class PatientEmailInputSerializer(serializers.Serializer):
    asunto=serializers.CharField()
    mensaje=serializers.CharField()

class PatientEmailView(OwnedPatientMixin, APIView):
    def post(self,request,patient_id):
        patient=self.patient(request,patient_id); serializer=PatientEmailInputSerializer(data=request.data); serializer.is_valid(raise_exception=True)
        send_patient_email(patient=patient,user=request.user,subject=serializer.validated_data['asunto'],message=serializer.validated_data['mensaje'])
        return Response({'detail':f'Correo enviado exitosamente a {patient.email}.'})

class PatientExportView(APIView):
    def get(self,request): return export_patients(request.user)
class ConsultationExportView(APIView):
    def get(self,request): return export_consultations(request.user)
class ClinicalImageExportView(APIView):
    def get(self,request): return export_images(request.user)

class DiagnosticsView(APIView):
    def get(self,request):
        images=ImagenesClinicas.objects.filter(paciente__medico=request.user).select_related('paciente').order_by('-fecha_subida')
        patient=request.query_params.get('patient'); image_type=request.query_params.get('type'); date=request.query_params.get('date')
        if patient: images=images.filter(paciente__nombre__icontains=patient)
        if image_type: images=images.filter(tipo_imagen=image_type)
        if date: images=images.filter(fecha_subida__date=date)
        total=images.count(); processed=images.filter(resultados__isnull=False).exclude(resultados='').count()
        paginator=PatientPagination(); page=paginator.paginate_queryset(images,request)
        response=paginator.get_paginated_response(ClinicalImageSerializer(page,many=True).data)
        response.data['statistics']={'total':total,'processed':processed,'pending':total-processed,'processed_percentage':round(processed/total*100,2) if total else 0,'type_count':images.values('tipo_imagen').distinct().count()}
        return response

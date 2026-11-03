from rest_framework import serializers
from django.urls import reverse

from Citas.models import Cita
from Pacientes.models import AntescedentesMedicos, Consentimiento, Consulta, EstudioComparativo, ImagenesClinicas, Odontograma, Paciente
from Usuarios.models import Perfil
from .services.patients import create_patient, legacy_age, update_patient
from .services.consultations import create_consultation
from .services.appointments import save_appointment
from .services.clinical_images import create_clinical_image
from .policies import scoped
from .upload_policy import validate_upload
from django.core.exceptions import ValidationError as DjangoValidationError
from .services.odontogram import validate_odontogram

class UploadValidationMixin:
    upload_fields = ()

    def to_internal_value(self, data):
        for field in self.upload_fields:
            uploaded = data.get(field)
            if uploaded is not None and hasattr(uploaded, 'read'):
                try:
                    validate_upload(uploaded)
                except DjangoValidationError as exc:
                    raise serializers.ValidationError({field: exc.messages}) from exc
        return super().to_internal_value(data)


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Perfil
        fields = ('clinica_nombre', 'telefono', 'direccion', 'extra')


class SessionUserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    email = serializers.EmailField()
    is_staff = serializers.BooleanField()
    profile = serializers.SerializerMethodField()
    can_access_backoffice = serializers.SerializerMethodField()

    def get_can_access_backoffice(self, user):
        from .policies import can_access_backoffice
        return can_access_backoffice(user)

    def get_profile(self, user):
        profile = Perfil.objects.filter(user=user).first()
        return ProfileSerializer(profile).data if profile else None


class DashboardPatientSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Paciente
        fields = ('id', 'nombre', 'appat', 'apmat', 'full_name', 'estatus')

    def get_full_name(self, patient):
        return f'{patient.nombre} {patient.appat} {patient.apmat}'.strip()


class DashboardAppointmentSerializer(serializers.ModelSerializer):
    paciente = DashboardPatientSerializer(read_only=True)

    class Meta:
        model = Cita
        fields = (
            'id', 'paciente', 'fecha', 'hora', 'motivo', 'estatus',
            'observaciones', 'created', 'updated',
        )


class PatientSerializer(serializers.ModelSerializer):
    age = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Paciente
        fields = (
            'id', 'nombre', 'appat', 'apmat', 'fecha_nacimiento', 'genero',
            'telefono', 'email', 'estatus', 'created', 'updated', 'age',
        )
        read_only_fields = ('id', 'created', 'updated', 'age')
        validators = []

    def get_age(self, patient):
        return legacy_age(patient)

    def create(self, validated_data):
        return create_patient(
            medico=self.context['request'].user,
            validated_data=validated_data,
        )

    def update(self, instance, validated_data):
        return update_patient(
            patient=instance,
            medico=self.context['request'].user,
            validated_data=validated_data,
        )


class MedicalHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = AntescedentesMedicos
        exclude = ('medico',)
        read_only_fields = ('id', 'paciente', 'created', 'updated', 'version')


class ConsultationSerializer(serializers.ModelSerializer):
    paciente = DashboardPatientSerializer(read_only=True)

    class Meta:
        model = Consulta
        fields = (
            'id', 'paciente', 'fecha_consulta', 'motivo_consulta',
            'diagnostico', 'tratamiento', 'observaciones',
        )
        read_only_fields = ('id', 'paciente', 'fecha_consulta')
        extra_kwargs = {
            'diagnostico': {'required': False, 'allow_blank': True},
            'tratamiento': {'required': False, 'allow_blank': True},
            'observaciones': {'required': False, 'allow_blank': True},
        }

    def create(self, validated_data):
        return create_consultation(
            patient=self.context['patient'],
            medico=self.context['request'].user,
            validated_data=validated_data,
        )


class AppointmentSerializer(serializers.ModelSerializer):
    paciente = DashboardPatientSerializer(read_only=True)
    paciente_id = serializers.IntegerField(write_only=True)
    estatus_display = serializers.CharField(source='get_estatus_display', read_only=True)

    class Meta:
        model = Cita
        fields = (
            'id', 'paciente', 'paciente_id', 'fecha', 'hora', 'motivo',
            'estatus', 'estatus_display', 'observaciones', 'created', 'updated',
        )
        read_only_fields = ('id', 'created', 'updated')
        extra_kwargs = {
            'motivo': {'required': False, 'allow_blank': True},
            'observaciones': {'required': False, 'allow_blank': True},
            'estatus': {'required': False},
        }

    def validate_paciente_id(self, value):
        if not scoped(self.context['request'].user, Paciente).filter(pk=value).exists():
            raise serializers.ValidationError('Paciente no encontrado.')
        return value

    def create(self, validated_data):
        patient = scoped(self.context['request'].user, Paciente).get(pk=validated_data.pop('paciente_id'))
        return save_appointment(user=self.context['request'].user, patient=patient, validated_data=validated_data)

    def update(self, instance, validated_data):
        patient_id = validated_data.pop('paciente_id', None)
        patient = scoped(self.context['request'].user, Paciente).get(pk=patient_id) if patient_id is not None else None
        return save_appointment(user=self.context['request'].user, appointment=instance, patient=patient, validated_data=validated_data)


class ClinicalImageSerializer(UploadValidationMixin, serializers.ModelSerializer):
    upload_fields = ('imagen',)
    consulta_id = serializers.IntegerField(write_only=True)
    imagen_url = serializers.SerializerMethodField(read_only=True)
    resultados_url = serializers.SerializerMethodField(read_only=True)
    patient_name = serializers.CharField(source='paciente.__str__', read_only=True)

    class Meta:
        model = ImagenesClinicas
        fields = (
            'id', 'paciente', 'patient_name', 'consulta', 'consulta_id', 'tipo_imagen',
            'descripcion', 'imagen', 'imagen_url',
            'resultados_url', 'fecha_subida',
        )
        read_only_fields = (
            'id', 'paciente', 'consulta', 'fecha_subida',
        )
        extra_kwargs = {
            'imagen': {'write_only': True, 'required': True},
            'tipo_imagen': {'required': True, 'allow_blank': False},
            'descripcion': {'required': True, 'allow_blank': False},
        }

    def get_imagen_url(self, image):
        return reverse('api-clinical-image-file', args=[image.pk]) if image.imagen else None

    def get_resultados_url(self, image):
        return reverse('api-clinical-image-result-file', args=[image.pk]) if image.resultados else None

    def create(self, validated_data):
        return create_clinical_image(
            patient=self.context['patient'],
            medico=self.context['request'].user,
            validated_data=validated_data,
        )


class OdontogramSerializer(serializers.ModelSerializer):
    denticion_permanente = serializers.JSONField(source='dientes_permanentes')
    denticion_decidua = serializers.JSONField(source='dientes_deciduos')
    resumen = serializers.JSONField(source='resumen_clinico')

    class Meta:
        model = Odontograma
        fields = ('id', 'denticion_permanente', 'denticion_decidua', 'resumen', 'created', 'updated', 'version')
        read_only_fields = ('id', 'created', 'updated', 'version')

    def to_internal_value(self, data):
        unknown = set(data) - set(self.fields)
        if unknown:
            raise serializers.ValidationError({'detail': 'El odontograma contiene campos desconocidos.'})
        return super().to_internal_value(data)

    def validate(self, attrs):
        validate_odontogram(attrs.get('dientes_permanentes', {}), attrs.get('dientes_deciduos', {}), attrs.get('resumen_clinico', {}))
        return attrs


STUDY_IMAGE_FIELDS = ('antes_oclusal_superior','antes_lateral_izquierda','antes_frontal','antes_lateral_derecha','antes_oclusal_inferior','despues_perfil','despues_semiperfil','despues_retrato_frontal','despues_retrato_sonrisa')

class ComparativeStudySerializer(UploadValidationMixin, serializers.ModelSerializer):
    upload_fields = STUDY_IMAGE_FIELDS
    image_urls = serializers.SerializerMethodField(read_only=True)
    class Meta:
        model = EstudioComparativo
        fields = ('id','paciente','fecha_inicio','diagnostico','observaciones',*STUDY_IMAGE_FIELDS,'image_urls','fecha_creacion','fecha_actualizacion')
        read_only_fields = ('id','paciente','image_urls','fecha_creacion','fecha_actualizacion')
        extra_kwargs = {field: {'write_only': True, 'required': False} for field in STUDY_IMAGE_FIELDS}
    def get_image_urls(self, study):
        return {field: reverse('api-comparative-study-image', args=[study.paciente_id, field]) if getattr(study, field) else None for field in STUDY_IMAGE_FIELDS}
    def validate(self, attrs):
        if self.instance is None:
            missing=[field for field in STUDY_IMAGE_FIELDS[:5] if not attrs.get(field)]
            if missing: raise serializers.ValidationError({field:['Este archivo es obligatorio.'] for field in missing})
        return attrs

class ConsentSerializer(serializers.ModelSerializer):
    archivo_ine_url=serializers.SerializerMethodField(read_only=True)
    pdf_generado=serializers.SerializerMethodField()
    class Meta:
        model=Consentimiento
        fields=('id','paciente','texto','fecha_aceptacion','archivo_ine','archivo_ine_url','pdf_generado')
        read_only_fields=('id','paciente','fecha_aceptacion','archivo_ine_url','pdf_generado')
        extra_kwargs={'archivo_ine':{'write_only':True,'required':False},'texto':{'required':False,'allow_blank':True}}
    def get_archivo_ine_url(self, consent): return reverse('api-consent-file', args=[consent.paciente_id]) if consent.archivo_ine else None
    def get_pdf_generado(self, consent): return reverse('api-consent-pdf', args=[consent.paciente_id]) if consent.pdf_generado else None

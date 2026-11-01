from rest_framework import serializers

from Citas.models import Cita
from Pacientes.models import AntescedentesMedicos, Consentimiento, Consulta, EstudioComparativo, ImagenesClinicas, Odontograma, Paciente
from Usuarios.models import Perfil
from .services.patients import create_patient, legacy_age, update_patient
from .services.consultations import create_consultation
from .services.appointments import save_appointment
from .services.clinical_images import create_clinical_image


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

    def get_profile(self, user):
        profile, _ = Perfil.objects.get_or_create(user=user)
        return ProfileSerializer(profile).data


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
        read_only_fields = ('id', 'paciente', 'created', 'updated')


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
        if not Paciente.objects.filter(pk=value, medico=self.context['request'].user).exists():
            raise serializers.ValidationError('Paciente no encontrado.')
        return value

    def create(self, validated_data):
        patient = Paciente.objects.get(pk=validated_data.pop('paciente_id'))
        return save_appointment(patient=patient, validated_data=validated_data)

    def update(self, instance, validated_data):
        patient_id = validated_data.pop('paciente_id', instance.paciente_id)
        patient = Paciente.objects.get(pk=patient_id)
        return save_appointment(appointment=instance, patient=patient, validated_data=validated_data)


class ClinicalImageSerializer(serializers.ModelSerializer):
    consulta_id = serializers.IntegerField(write_only=True)
    imagen_url = serializers.SerializerMethodField(read_only=True)
    resultados_url = serializers.SerializerMethodField(read_only=True)
    patient_name = serializers.CharField(source='paciente.__str__', read_only=True)

    class Meta:
        model = ImagenesClinicas
        fields = (
            'id', 'paciente', 'patient_name', 'consulta', 'consulta_id', 'tipo_imagen',
            'descripcion', 'imagen', 'imagen_url', 'resultados',
            'resultados_url', 'fecha_subida',
        )
        read_only_fields = (
            'id', 'paciente', 'consulta', 'resultados', 'fecha_subida',
        )
        extra_kwargs = {
            'imagen': {'write_only': True, 'required': True},
            'tipo_imagen': {'required': True, 'allow_blank': False},
            'descripcion': {'required': True, 'allow_blank': False},
        }

    def get_imagen_url(self, image):
        return image.imagen.url if image.imagen else None

    def get_resultados_url(self, image):
        return image.resultados.url if image.resultados else None

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
        fields = ('id', 'denticion_permanente', 'denticion_decidua', 'resumen', 'created', 'updated')
        read_only_fields = ('id', 'created', 'updated')


STUDY_IMAGE_FIELDS = ('antes_oclusal_superior','antes_lateral_izquierda','antes_frontal','antes_lateral_derecha','antes_oclusal_inferior','despues_perfil','despues_semiperfil','despues_retrato_frontal','despues_retrato_sonrisa')

class ComparativeStudySerializer(serializers.ModelSerializer):
    image_urls = serializers.SerializerMethodField(read_only=True)
    class Meta:
        model = EstudioComparativo
        fields = ('id','paciente','fecha_inicio','diagnostico','observaciones',*STUDY_IMAGE_FIELDS,'image_urls','fecha_creacion','fecha_actualizacion')
        read_only_fields = ('id','paciente','image_urls','fecha_creacion','fecha_actualizacion')
        extra_kwargs = {field: {'write_only': True, 'required': False} for field in STUDY_IMAGE_FIELDS}
    def get_image_urls(self, study):
        return {field: getattr(study, field).url if getattr(study, field) else None for field in STUDY_IMAGE_FIELDS}
    def validate(self, attrs):
        if self.instance is None:
            missing=[field for field in STUDY_IMAGE_FIELDS[:5] if not attrs.get(field)]
            if missing: raise serializers.ValidationError({field:['Este archivo es obligatorio.'] for field in missing})
        return attrs

class ConsentSerializer(serializers.ModelSerializer):
    archivo_ine_url=serializers.SerializerMethodField(read_only=True)
    class Meta:
        model=Consentimiento
        fields=('id','paciente','texto','fecha_aceptacion','archivo_ine','archivo_ine_url','pdf_generado')
        read_only_fields=('id','paciente','fecha_aceptacion','archivo_ine_url','pdf_generado')
        extra_kwargs={'archivo_ine':{'write_only':True,'required':False},'texto':{'required':False,'allow_blank':True}}
    def get_archivo_ine_url(self, consent): return consent.archivo_ine.url if consent.archivo_ine else None

from rest_framework.exceptions import ValidationError

from Pacientes.models import Consulta, ImagenesClinicas


def create_clinical_image(*, patient, medico, validated_data):
    consultation_id = validated_data.pop('consulta_id')
    try:
        consultation = Consulta.objects.get(
            pk=consultation_id, paciente=patient, medico=medico,
        )
    except Consulta.DoesNotExist as exc:
        raise ValidationError({'consulta_id': ['Debes seleccionar una consulta válida.']}) from exc
    return ImagenesClinicas.objects.create(
        paciente=patient,
        consulta=consultation,
        medico=medico,
        tipo_imagen=validated_data['tipo_imagen'].strip().upper(),
        descripcion=validated_data['descripcion'].strip().upper(),
        imagen=validated_data['imagen'],
    )

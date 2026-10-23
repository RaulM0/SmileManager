from django.utils import timezone

from Pacientes.models import Consulta


def create_consultation(*, patient, medico, validated_data):
    return Consulta.objects.create(
        paciente=patient,
        medico=medico,
        fecha_consulta=timezone.now(),
        motivo_consulta=validated_data.get('motivo_consulta', '').upper(),
        diagnostico=validated_data.get('diagnostico', 'Ninguno').upper(),
        tratamiento=validated_data.get('tratamiento', 'Ninguno').upper(),
        observaciones=validated_data.get('observaciones', 'Ninguna').upper(),
    )

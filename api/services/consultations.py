from django.utils import timezone
from django.db import transaction

from Pacientes.models import Consulta
from .clinical_access import lock_authorized_patient


@transaction.atomic
def create_consultation(*, patient, medico, validated_data, clinic_id=None):
    patient = lock_authorized_patient(user=medico, patient_id=patient.pk, clinic_id=clinic_id)
    return Consulta.objects.create(
        paciente=patient,
        medico=medico,
        fecha_consulta=timezone.now(),
        motivo_consulta=validated_data.get('motivo_consulta', '').upper(),
        diagnostico=validated_data.get('diagnostico', 'Ninguno').upper(),
        tratamiento=validated_data.get('tratamiento', 'Ninguno').upper(),
        observaciones=validated_data.get('observaciones', 'Ninguna').upper(),
    )

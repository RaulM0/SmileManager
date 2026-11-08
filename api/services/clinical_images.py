import logging

from rest_framework.exceptions import ValidationError
from django.db import transaction

from Pacientes.models import Consulta, ImagenesClinicas
from .clinical_access import lock_authorized_patient

logger = logging.getLogger(__name__)


@transaction.atomic
def create_clinical_image(*, patient, medico, validated_data, clinic_id=None):
    patient = lock_authorized_patient(user=medico, patient_id=patient.pk, clinic_id=clinic_id)
    consultation_id = validated_data.pop('consulta_id')
    try:
        consultation = Consulta.objects.get(
            pk=consultation_id, paciente=patient, medico=medico,
        )
    except Consulta.DoesNotExist as exc:
        raise ValidationError({'consulta_id': ['Debes seleccionar una consulta válida.']}) from exc
    image = ImagenesClinicas(
        paciente=patient,
        consulta=consultation,
        medico=medico,
        tipo_imagen=validated_data['tipo_imagen'].strip().upper(),
        descripcion=validated_data['descripcion'].strip().upper(),
        imagen=validated_data['imagen'],
    )
    try:
        image.save()
    except Exception:
        if image.imagen and image.imagen._committed:
            try:
                image.imagen.delete(save=False)
            except Exception:
                logger.exception('No fue posible limpiar un archivo clínico después de un error de persistencia.')
        raise
    return image

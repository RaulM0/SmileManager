from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import APIException, ValidationError

from Pacientes.models import AntescedentesMedicos, ClinicalRevision, Odontograma, Paciente
from api.policies import consistent_or_404, scoped
from api.services.odontogram import validate_odontogram


class ConcurrentModification(APIException):
    status_code = 409
    default_detail = 'Este expediente fue actualizado desde otra sesión. Recarga la información antes de guardar tus cambios.'
    default_code = 'concurrent_modification'


class ClinicalDataConflict(APIException):
    status_code = 409
    default_detail = 'Hay registros clínicos duplicados que requieren revisión antes de editar.'
    default_code = 'clinical_data_conflict'


def snapshot(obj):
    excluded = {'id', 'paciente', 'medico', 'created', 'updated', 'version'}
    return {field.name: getattr(obj, field.name) for field in obj._meta.concrete_fields if field.name not in excluded}


@transaction.atomic
def save_record(*, user, patient_id, model, changes, expected_version):
    if model not in (AntescedentesMedicos, Odontograma):
        raise ValueError('Recurso clínico no soportado')
    if isinstance(expected_version, bool) or not isinstance(expected_version, int) or expected_version < 0:
        raise ValidationError({'version': ['Debe indicar la versión obtenida al consultar el expediente.']})
    # Lock the stable parent even before the first clinical row exists.
    patient = get_object_or_404(scoped(user, Paciente).select_for_update(), pk=patient_id)
    rows = list(consistent_or_404(user, model, patient).select_for_update()[:2])
    if len(rows) > 1:
        raise ClinicalDataConflict()
    obj = rows[0] if rows else model(paciente=patient, medico=user)
    if obj.version != expected_version:
        raise ConcurrentModification()
    if model is Odontograma and obj.pk:
        try:
            validate_odontogram(obj.dientes_permanentes, obj.dientes_deciduos, obj.resumen_clinico)
        except ValidationError as exc:
            raise ClinicalDataConflict('El odontograma previo requiere revisión o migración antes de editarse.') from exc
    resource_type = 'medical_history' if model is AntescedentesMedicos else 'odontogram'
    if obj.pk:
        ClinicalRevision.objects.get_or_create(resource_type=resource_type, resource_id=obj.pk, version=obj.version,
                                               defaults={'patient': patient, 'actor': None, 'snapshot': snapshot(obj)})
    for key, value in changes.items():
        setattr(obj, key, value)
    obj.version += 1
    obj.save()
    ClinicalRevision.objects.create(resource_type=resource_type, resource_id=obj.pk, version=obj.version,
                                    patient=patient, actor=user, snapshot=snapshot(obj))
    return obj

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import APIException, ValidationError

from Pacientes.models import AntescedentesMedicos, ClinicalRevision, Odontograma, Paciente
from Pacientes.access import clinic_clinical_queryset, consistent_or_404, scoped
from api.services.odontogram import validate_odontogram
from .document_integrity import seal, verify, digest
from .document_payloads import revision_payload


def sealed_revision(*, actor, **values):
    revision = ClinicalRevision(actor=actor, actor_name=(actor.get_full_name() or actor.username) if actor else '', **values)
    revision.content_sha256, revision.integrity_seal = seal(revision_payload(revision))
    revision.save()
    return revision


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
def save_record(*, user, patient_id, model, changes, expected_version, clinic_id=None):
    if model not in (AntescedentesMedicos, Odontograma):
        raise ValueError('Recurso clínico no soportado')
    if isinstance(expected_version, bool) or not isinstance(expected_version, int) or expected_version < 0:
        raise ValidationError({'version': ['Debe indicar la versión obtenida al consultar el expediente.']})
    # Lock the stable parent even before the first clinical row exists.
    patients = clinic_clinical_queryset(user, clinic_id, Paciente) if clinic_id is not None else scoped(user, Paciente)
    patient = get_object_or_404(patients.select_for_update(of=('self',)), pk=patient_id)
    rows = list(consistent_or_404(user, model, patient, clinic_id=clinic_id).select_for_update(of=('self',))[:2])
    if len(rows) > 1:
        raise ClinicalDataConflict()
    obj = rows[0] if rows else model(paciente=patient, medico=user)
    if obj.version != expected_version:
        raise ConcurrentModification()
    current_revision = ClinicalRevision.objects.filter(resource_type='medical_history' if model is AntescedentesMedicos else 'odontogram', resource_id=obj.pk, version=obj.version).first() if obj.pk else None
    if current_revision and current_revision.content_sha256 and (
            not verify(revision_payload(current_revision), current_revision.content_sha256, current_revision.integrity_seal)
            or digest(current_revision.snapshot) != digest(snapshot(obj))):
        raise ClinicalDataConflict('El expediente no coincide con su última revisión. Requiere revisión de integridad.')
    if model is Odontograma and obj.pk:
        try:
            validate_odontogram(obj.dientes_permanentes, obj.dientes_deciduos, obj.resumen_clinico)
        except ValidationError as exc:
            raise ClinicalDataConflict('El odontograma previo requiere revisión o migración antes de editarse.') from exc
    resource_type = 'medical_history' if model is AntescedentesMedicos else 'odontogram'
    if obj.pk and ClinicalRevision.objects.filter(resource_type=resource_type, resource_id=obj.pk).exclude(
            patient_id=patient.pk, clinic_id=patient.clinic_id).exists():
        raise ClinicalDataConflict('El historial de versiones requiere conciliación antes de editarse.')
    if obj.pk:
        if not ClinicalRevision.objects.filter(resource_type=resource_type, resource_id=obj.pk, version=obj.version).exists():
            sealed_revision(resource_type=resource_type, resource_id=obj.pk, version=obj.version,
                            patient=patient, clinic_id=patient.clinic_id, actor=None, snapshot=snapshot(obj))
    for key, value in changes.items():
        setattr(obj, key, value)
    obj.version += 1
    obj.save()
    sealed_revision(resource_type=resource_type, resource_id=obj.pk, version=obj.version,
                    patient=patient, clinic_id=patient.clinic_id, actor=user, snapshot=snapshot(obj))
    return obj

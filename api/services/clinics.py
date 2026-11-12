"""Clinic state changes. Caller must authorize and audit the administrative action."""
from django.core.exceptions import ValidationError
from django.db import transaction

from Usuarios.models import Clinic


@transaction.atomic
def transition_clinic(*, clinic_id, target):
    clinic = Clinic.objects.select_for_update().get(pk=clinic_id)
    transitions = {
        Clinic.Status.INACTIVE: {Clinic.Status.ACTIVE},
        Clinic.Status.ACTIVE: {Clinic.Status.SUSPENDED, Clinic.Status.INACTIVE},
        Clinic.Status.SUSPENDED: {Clinic.Status.ACTIVE, Clinic.Status.INACTIVE},
    }
    if target != clinic.status and target not in transitions.get(clinic.status, set()):
        raise ValidationError('Transición de clínica no válida.')
    if target != clinic.status:
        clinic.invitations.filter(activates_clinic=True).update(activates_clinic=False)
        clinic.status = target
        clinic.save(update_fields=['status', 'updated_at'])
    return clinic

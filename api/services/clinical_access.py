"""Authorization boundary for clinical services accepting patient objects."""
from django.shortcuts import get_object_or_404

from Pacientes.models import Paciente
from Pacientes.access import clinic_clinical_queryset, scoped
from Usuarios.clinic_context import lock_clinic_capability


def lock_authorized_patient(*, user, patient_id, clinic_id):
    """Caller must hold an atomic transaction; never trust an object from a caller."""
    if clinic_id is None:
        rows = scoped(user, Paciente)
    else:
        lock_clinic_capability(user, clinic_id, 'clinical.assigned')
        rows = clinic_clinical_queryset(user, clinic_id, Paciente)
    return get_object_or_404(rows.select_for_update(of=('self',)), pk=patient_id)

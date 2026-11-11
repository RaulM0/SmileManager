"""Shared HTTP context and audit hooks for clinic endpoints."""
from rest_framework.permissions import IsAuthenticated

from Usuarios.models import AuditEvent
from Usuarios.clinic_context import lock_clinic_capability, require_clinic_capability


class TenantClinicalContextMixin:
    permission_classes = [IsAuthenticated]

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        self.membership = require_clinic_capability(request.user, request.headers.get('X-Clinic-ID'), 'clinical.assigned')

    def lock_context(self):
        """Serialize writes with clinic and membership transitions using their lock order."""
        self.membership = lock_clinic_capability(self.request.user, self.membership.clinic_id, 'clinical.assigned')
        return self.membership.clinic

    def record(self, resource, action, resource_type='patient', outcome='success'):
        AuditEvent.objects.create(actor=self.request.user, clinic_id=self.membership.clinic_id,
                                  action=action, resource_type=resource_type, resource_id=str(resource.pk),
                                  request_id=self.request._request.request_id, outcome=outcome)

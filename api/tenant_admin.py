"""Clinic administration lists; no clinical snapshots or storage keys."""
from django.db.models import Exists
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from Usuarios.models import AuditEvent, Clinic, ClinicInvitation, ClinicMembership
from .backoffice import Pagination
from .tenant_context import require_clinic_capability


class TenantAdminList(APIView):
    permission_classes = [IsAuthenticated]
    capability = 'membership.manage'

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        self.membership = require_clinic_capability(request.user, request.headers.get('X-Clinic-ID'), self.capability)

    def live_rows(self, rows):
        allowed = ClinicMembership.objects.filter(clinic_id=self.membership.clinic_id, user_id=self.request.user.pk,
                                                  user__is_active=True, clinic__status=Clinic.Status.ACTIVE,
                                                  status=ClinicMembership.Status.ACTIVE,
                                                  role=ClinicMembership.Role.CLINIC_ADMIN)
        return rows.alias(_tenant_admin_active=Exists(allowed)).filter(_tenant_admin_active=True)

    def paginated(self, rows, serializer):
        paginator = Pagination()
        page = paginator.paginate_queryset(rows, self.request, view=self)
        return paginator.get_paginated_response([serializer(item) for item in page])


@method_decorator(never_cache, name='dispatch')
class ClinicMembers(TenantAdminList):
    def get(self, request):
        rows = self.live_rows(ClinicMembership.objects.filter(clinic_id=self.membership.clinic_id).select_related('user')).order_by('user__username', 'pk')
        return self.paginated(rows, lambda row: {'id': str(row.pk), 'user_id': row.user_id,
                                               'username': row.user.username, 'email': row.user.email,
                                               'user_active': row.user.is_active, 'role': row.role,
                                               'status': row.status, 'joined_at': row.joined_at})


@method_decorator(never_cache, name='dispatch')
class ClinicInvitations(TenantAdminList):
    def get(self, request):
        rows = self.live_rows(ClinicInvitation.objects.filter(clinic_id=self.membership.clinic_id)).order_by('-created_at', '-pk')
        return self.paginated(rows, lambda row: {'id': str(row.pk), 'email': row.email, 'role': row.role,
                                               'status': row.status, 'created_at': row.created_at,
                                               'expires_at': row.expires_at, 'resolved_at': row.resolved_at})


@method_decorator(never_cache, name='dispatch')
class ClinicAudit(TenantAdminList):
    capability = 'clinic.audit'

    def get(self, request):
        rows = self.live_rows(AuditEvent.objects.filter(clinic_id=self.membership.clinic_id).select_related('actor'))
        action = request.query_params.get('action', '').strip()[:64]
        if action:
            rows = rows.filter(action=action)
        rows = rows.order_by('-timestamp', '-pk')
        response = self.paginated(rows, lambda row: {'id': row.pk, 'timestamp': row.timestamp,
                                                    'actor_id': row.actor_id,
                                                    'actor': row.actor.username if row.actor_id else None,
                                                    'action': row.action, 'resource_type': row.resource_type,
                                                    'resource_id': row.resource_id, 'outcome': row.outcome,
                                                    'request_id': row.request_id})
        AuditEvent.objects.create(actor=request.user, clinic_id=self.membership.clinic_id,
                                  action='TENANT_AUDIT_VIEWED', resource_type='audit',
                                  request_id=request._request.request_id)
        return response

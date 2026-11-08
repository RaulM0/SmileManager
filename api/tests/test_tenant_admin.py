import uuid
from datetime import timedelta

from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from Usuarios.models import AuditEvent, Clinic, ClinicInvitation, ClinicMembership, PlatformAdmin


class TenantAdminTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user('tenant-admin')
        self.other = User.objects.create_user('tenant-other-admin')
        self.doctor = User.objects.create_user('tenant-admin-doctor')
        self.platform = User.objects.create_user('tenant-platform')
        PlatformAdmin.objects.create(user=self.platform, is_active=True)
        self.a = Clinic.objects.create(name='A', slug='tenant-admin-a', status='ACTIVE')
        self.b = Clinic.objects.create(name='B', slug='tenant-admin-b', status='ACTIVE')
        self.membership = ClinicMembership.objects.create(user=self.admin, clinic=self.a, role='CLINIC_ADMIN', status='ACTIVE')
        ClinicMembership.objects.create(user=self.other, clinic=self.b, role='CLINIC_ADMIN', status='ACTIVE')
        ClinicMembership.objects.create(user=self.doctor, clinic=self.a, role='DOCTOR', status='ACTIVE')
        for index, clinic in enumerate((self.a, self.b)):
            ClinicInvitation.objects.create(clinic=clinic, email=f'{index}@example.test', role='DOCTOR', token_hash=str(index)*64,
                                            invited_by=self.admin, expires_at=timezone.now()+timedelta(days=1))
            AuditEvent.objects.create(clinic=clinic, actor=self.admin, action=f'SYNTHETIC_{index}', request_id=uuid.uuid4())
        self.client.force_authenticate(self.admin)

    def test_members_invitations_and_audit_are_confined_to_clinic(self):
        members = self.client.get(reverse('tenant-admin-memberships'), HTTP_X_CLINIC_ID=str(self.a.pk))
        self.assertEqual(members.status_code, 200)
        self.assertEqual({row['username'] for row in members.data['results']}, {'tenant-admin', 'tenant-admin-doctor'})
        invitations = self.client.get(reverse('tenant-admin-invitations'), HTTP_X_CLINIC_ID=str(self.a.pk))
        self.assertEqual(invitations.data['count'], 1)
        self.assertNotIn('token_hash', invitations.data['results'][0])
        audit = self.client.get(reverse('tenant-admin-audit'), HTTP_X_CLINIC_ID=str(self.a.pk))
        self.assertEqual([row['action'] for row in audit.data['results']], ['SYNTHETIC_0'])
        self.assertTrue(AuditEvent.objects.filter(clinic=self.a, actor=self.admin, action='TENANT_AUDIT_VIEWED').exists())
        self.assertEqual(self.client.get(reverse('tenant-admin-memberships'), HTTP_X_CLINIC_ID=str(self.b.pk)).status_code, 403)

    def test_doctor_platform_and_revoked_admin_cannot_read_clinic_audit(self):
        url = reverse('tenant-admin-audit')
        for user in (self.doctor, self.platform):
            self.client.force_authenticate(user)
            self.assertEqual(self.client.get(url, HTTP_X_CLINIC_ID=str(self.a.pk)).status_code, 403)
        self.client.force_authenticate(self.admin)
        self.membership.status = 'REVOKED'
        self.membership.save(update_fields=['status'])
        self.assertEqual(self.client.get(url, HTTP_X_CLINIC_ID=str(self.a.pk)).status_code, 403)

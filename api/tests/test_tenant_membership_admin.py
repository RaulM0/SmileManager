import json
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor

from django.contrib.auth.models import User
from django.db import close_old_connections
from django.test import TestCase, TransactionTestCase, skipUnlessDBFeature
from django.urls import reverse
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from rest_framework_simplejwt.tokens import RefreshToken

from api.services.memberships import change_membership, MembershipConflict
from Usuarios.models import AuditEvent, Clinic, ClinicMembership


class MembershipAdminTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user('clinic-admin')
        self.doctor = User.objects.create_user('doctor')
        self.clinic = Clinic.objects.create(name='A', slug='a', status='ACTIVE')
        self.other = Clinic.objects.create(name='B', slug='b', status='ACTIVE')
        self.admin_member = ClinicMembership.objects.create(clinic=self.clinic, user=self.admin, role='CLINIC_ADMIN', status='ACTIVE', joined_at=timezone.now())
        self.doctor_member = ClinicMembership.objects.create(clinic=self.clinic, user=self.doctor, role='DOCTOR', status='ACTIVE', joined_at=timezone.now())
        self.token = str(RefreshToken.for_user(self.admin).access_token)

    def patch_member(self, member, data, clinic=None, token=None):
        return self.client.patch(reverse('clinic-membership-detail', args=[member.pk]), data=json.dumps(data), content_type='application/json', HTTP_AUTHORIZATION=f'Bearer {token or self.token}', HTTP_X_CLINIC_ID=str((clinic or self.clinic).pk))

    def test_suspend_and_audit_then_reactivate(self):
        response = self.patch_member(self.doctor_member, {'status': 'SUSPENDED'})
        self.assertEqual(response.status_code, 200)
        event = AuditEvent.objects.get(action='CLINIC_MEMBERSHIP_CHANGED')
        self.assertEqual(event.clinic, self.clinic)
        self.assertEqual(event.actor, self.admin)
        self.assertEqual(self.patch_member(self.doctor_member, {'status': 'ACTIVE'}).status_code, 200)

    def test_last_administrator_and_privilege_escalation_denied(self):
        self.assertEqual(self.patch_member(self.admin_member, {'status': 'REVOKED'}).status_code, 409)
        self.assertEqual(self.patch_member(self.doctor_member, {'role': 'PLATFORM_ADMIN'}).status_code, 400)
        self.assertEqual(self.patch_member(self.doctor_member, {'status': 'ACTIVE', 'clinic': str(self.other.pk)}).status_code, 400)
        self.assertFalse(AuditEvent.objects.filter(action='CLINIC_MEMBERSHIP_CHANGED').exists())

    def test_cross_clinic_and_non_admin_denied(self):
        other_member = ClinicMembership.objects.create(clinic=self.other, user=self.doctor, role='STAFF', status='ACTIVE')
        self.assertEqual(self.patch_member(other_member, {'status': 'REVOKED'}).status_code, 404)
        doctor_token = str(RefreshToken.for_user(self.doctor).access_token)
        self.assertEqual(self.patch_member(self.admin_member, {'status': 'SUSPENDED'}, token=doctor_token).status_code, 403)

    def test_no_reactivation_without_acceptance_or_after_revocation(self):
        self.doctor_member.status = 'SUSPENDED'
        self.doctor_member.joined_at = None
        self.doctor_member.save(update_fields=['status', 'joined_at'])
        self.assertEqual(self.patch_member(self.doctor_member, {'status': 'ACTIVE'}).status_code, 409)
        self.doctor_member.status = 'REVOKED'
        self.doctor_member.joined_at = timezone.now()
        self.doctor_member.save(update_fields=['status', 'joined_at'])
        self.assertEqual(self.patch_member(self.doctor_member, {'status': 'ACTIVE'}).status_code, 409)

    def test_revoked_member_loses_context_with_existing_jwt(self):
        doctor_token = str(RefreshToken.for_user(self.doctor).access_token)
        self.assertEqual(self.patch_member(self.doctor_member, {'status': 'REVOKED'}).status_code, 200)
        response = self.client.get(reverse('clinic-context'), HTTP_AUTHORIZATION=f'Bearer {doctor_token}', HTTP_X_CLINIC_ID=str(self.clinic.pk))
        self.assertEqual(response.status_code, 403)


@skipUnlessDBFeature('has_select_for_update')
class MembershipConcurrencyTests(TransactionTestCase):
    def test_two_administrators_cannot_revoke_each_other(self):
        clinic = Clinic.objects.create(name='A', slug='a', status='ACTIVE')
        users = [User.objects.create_user('admin-a'), User.objects.create_user('admin-b')]
        members = [ClinicMembership.objects.create(clinic=clinic, user=user, role='CLINIC_ADMIN', status='ACTIVE', joined_at=timezone.now()) for user in users]
        barrier = threading.Barrier(2)

        def revoke(index):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                change_membership(actor=users[index], clinic_id=clinic.pk, membership_id=members[1-index].pk,
                                  role=None, status='REVOKED', request_id=uuid.uuid4())
                return 'success'
            except (MembershipConflict, PermissionDenied):
                return 'denied'
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(revoke, (0, 1)))
        self.assertCountEqual(results, ['success', 'denied'])
        self.assertEqual(ClinicMembership.objects.filter(clinic=clinic, role='CLINIC_ADMIN', status='ACTIVE').count(), 1)

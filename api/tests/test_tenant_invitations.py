import uuid
import threading
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.models import User
from django.db import close_old_connections
from django.test import TestCase, TransactionTestCase, override_settings, skipUnlessDBFeature
from django.core import mail
from django.urls import reverse
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError
from api.authentication import SessionRefreshToken as RefreshToken

from api.services.invitations import create_invitation, register_with_invitation, resolve_invitation, revoke_invitation
from api.services.memberships import MembershipConflict
from Usuarios.models import Clinic, ClinicInvitation, ClinicMembership


class InvitationTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user('admin', email='admin@example.com')
        self.user = User.objects.create_user('new', email='new@example.com')
        self.other = User.objects.create_user('other', email='other@example.com')
        self.clinic = Clinic.objects.create(name='A', slug='a', status='ACTIVE')
        ClinicMembership.objects.create(user=self.admin, clinic=self.clinic, role='CLINIC_ADMIN', status='ACTIVE')

    def invite(self):
        return create_invitation(actor=self.admin, clinic_id=self.clinic.pk, email='New@Example.com', role='DOCTOR', request_id=uuid.uuid4())

    def resolve(self, user, token, accept=True):
        return resolve_invitation(user=user, token=token, accept=accept, request_id=uuid.uuid4())

    def test_accept_once_and_hash_token(self):
        invitation, token = self.invite()
        self.assertNotEqual(invitation.token_hash, token)
        self.assertFalse(ClinicMembership.objects.filter(user=self.user).exists())
        self.resolve(self.user, token)
        membership = ClinicMembership.objects.get(user=self.user, clinic=self.clinic)
        self.assertEqual((membership.status, membership.role), ('ACTIVE', 'DOCTOR'))
        self.assertIsNotNone(membership.joined_at)
        with self.assertRaises(PermissionDenied):
            self.resolve(self.user, token)

    def test_wrong_user_expiration_and_revocation(self):
        invitation, token = self.invite()
        with self.assertRaises(PermissionDenied):
            self.resolve(self.other, token)
        invitation.expires_at = timezone.now() - timedelta(seconds=1)
        invitation.save(update_fields=['expires_at'])
        with self.assertRaises(PermissionDenied):
            self.resolve(self.user, token)
        replacement, replacement_token = self.invite()
        revoke_invitation(actor=self.admin, clinic_id=self.clinic.pk, invitation_id=replacement.pk, request_id=uuid.uuid4())
        with self.assertRaises(PermissionDenied):
            self.resolve(self.user, replacement_token)

    def test_duplicate_and_existing_membership_do_not_grant_role(self):
        invitation, token = self.invite()
        with self.assertRaises(MembershipConflict):
            self.invite()
        existing = ClinicMembership.objects.create(clinic=self.clinic, user=self.user, role='STAFF', status='ACTIVE')
        with self.assertRaises(MembershipConflict):
            self.resolve(self.user, token)
        existing.refresh_from_db()
        self.assertEqual(existing.role, 'STAFF')

    def test_reject_does_not_create_membership(self):
        invitation, token = self.invite()
        self.resolve(self.user, token, accept=False)
        invitation.refresh_from_db()
        self.assertEqual(invitation.status, ClinicInvitation.Status.REJECTED)
        self.assertFalse(ClinicMembership.objects.filter(user=self.user).exists())

    def test_register_new_account_and_consume_token_atomically(self):
        invitation, token = create_invitation(actor=self.admin, clinic_id=self.clinic.pk, email='new-account@example.com', role='DOCTOR', request_id=uuid.uuid4())
        url = reverse('clinic-invitation-register')
        response = self.client.post(url, data=json.dumps({'token': token, 'username': 'invited-person', 'password': 'Unique$Password987'}), content_type='application/json')
        self.assertEqual(response.status_code, 201)
        user = User.objects.get(username='invited-person')
        self.assertEqual(user.email, invitation.email)
        self.assertTrue(user.check_password('Unique$Password987'))
        self.assertTrue(ClinicMembership.objects.filter(user=user, clinic=self.clinic, status='ACTIVE', role='DOCTOR').exists())
        replay = self.client.post(url, data=json.dumps({'token': token, 'username': 'another', 'password': 'Unique$Password987'}), content_type='application/json')
        self.assertEqual(replay.status_code, 403)
        self.assertFalse(User.objects.filter(username='another').exists())

    def test_register_duplicate_username_preserves_pending_invitation(self):
        invitation, token = create_invitation(actor=self.admin, clinic_id=self.clinic.pk, email='new-account@example.com', role='DOCTOR', request_id=uuid.uuid4())
        response = self.client.post(reverse('clinic-invitation-register'), data=json.dumps({'token': token, 'username': self.admin.username, 'password': 'Unique$Password987'}), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        invitation.refresh_from_db()
        self.assertEqual(invitation.status, 'PENDING')

    def test_register_does_not_bypass_existing_account_membership(self):
        ClinicMembership.objects.create(clinic=self.clinic, user=self.user, role='DOCTOR', status='SUSPENDED')
        invitation, token = self.invite()
        response = self.client.post(reverse('clinic-invitation-register'), data=json.dumps({'token': token, 'username': 'replacement', 'password': 'Unique$Password987'}), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.filter(username='replacement').exists())
        invitation.refresh_from_db()
        self.assertEqual(invitation.status, 'PENDING')

    def test_public_registration_preview_does_not_disclose_email(self):
        invitation, token = self.invite()
        response = self.client.post(reverse('clinic-invitation-register-preview'), data=json.dumps({'token': token}), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'clinic': self.clinic.name, 'role': 'DOCTOR'})
        self.assertNotIn(invitation.email, response.content.decode())
        self.resolve(self.user, token, accept=False)
        response = self.client.post(reverse('clinic-invitation-register-preview'), data=json.dumps({'token': token}), content_type='application/json')
        self.assertEqual(response.status_code, 403)

    @override_settings(TENANT_INVITATION_URL='https://example.com/app/invitations/accept')
    def test_http_delivery_and_acceptance(self):
        admin_token = str(RefreshToken.for_user(self.admin, mfa_verified=True).access_token)
        response = self.client.post(reverse('clinic-invitation-create'),
            data=json.dumps({'email': self.user.email, 'role': 'DOCTOR'}), content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {admin_token}', HTTP_X_CLINIC_ID=str(self.clinic.pk))
        self.assertEqual(response.status_code, 202)
        self.assertEqual(len(mail.outbox), 1)
        token = mail.outbox[0].body.split('#', 1)[1].strip()
        self.assertNotIn(token, response.content.decode())
        user_token = str(RefreshToken.for_user(self.user).access_token)
        preview = self.client.post(reverse('clinic-invitation-preview'), data=json.dumps({'token': token}),
            content_type='application/json', HTTP_AUTHORIZATION=f'Bearer {user_token}')
        self.assertEqual(preview.status_code, 200)
        self.assertEqual(preview.json()['clinic'], 'A')
        response = self.client.post(reverse('clinic-invitation-resolve'),
            data=json.dumps({'token': token, 'action': 'accept'}), content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {user_token}')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(ClinicMembership.objects.filter(user=self.user, clinic=self.clinic, status='ACTIVE').exists())

    @override_settings(TENANT_INVITATION_URL='https://example.com/app/invitations/accept')
    @patch('api.tenant_views.send_mail', return_value=0)
    def test_failed_delivery_does_not_leave_invitation(self, _send):
        admin_token = str(RefreshToken.for_user(self.admin, mfa_verified=True).access_token)
        response = self.client.post(reverse('clinic-invitation-create'),
            data=json.dumps({'email': self.user.email, 'role': 'DOCTOR'}), content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {admin_token}', HTTP_X_CLINIC_ID=str(self.clinic.pk))
        self.assertEqual(response.status_code, 503)
        self.assertFalse(ClinicInvitation.objects.exists())


@skipUnlessDBFeature('has_select_for_update')
class InvitationConcurrencyTests(TransactionTestCase):
    def test_concurrent_invitations_create_only_one_pending(self):
        admin = User.objects.create_user('admin')
        clinic = Clinic.objects.create(name='A', slug='a', status='ACTIVE')
        ClinicMembership.objects.create(user=admin, clinic=clinic, role='CLINIC_ADMIN', status='ACTIVE')
        barrier = threading.Barrier(2)

        def invite(_):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                create_invitation(actor=admin, clinic_id=clinic.pk, email='person@example.com', role='DOCTOR', request_id=uuid.uuid4())
                return 'created'
            except MembershipConflict:
                return 'conflict'
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(invite, (0, 1)))
        self.assertCountEqual(results, ['created', 'conflict'])
        self.assertEqual(ClinicInvitation.objects.filter(status='PENDING').count(), 1)

    def test_one_registration_consumes_invitation(self):
        admin = User.objects.create_user('admin-register')
        clinic = Clinic.objects.create(name='A', slug='register-a', status='ACTIVE')
        ClinicMembership.objects.create(user=admin, clinic=clinic, role='CLINIC_ADMIN', status='ACTIVE')
        _, token = create_invitation(actor=admin, clinic_id=clinic.pk, email='invite@example.com', role='DOCTOR', request_id=uuid.uuid4())
        barrier = threading.Barrier(2)

        def register(index):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                register_with_invitation(token=token, username=f'candidate-{index}', password='Unique$Password987', request_id=uuid.uuid4())
                return 'created'
            except PermissionDenied:
                return 'denied'
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(register, (0, 1)))
        self.assertCountEqual(results, ['created', 'denied'])
        self.assertEqual(User.objects.filter(username__startswith='candidate-').count(), 1)
        self.assertEqual(ClinicMembership.objects.filter(clinic=clinic, role='DOCTOR', status='ACTIVE').count(), 1)

    def test_same_email_in_two_clinics_creates_only_one_account(self):
        admin = User.objects.create_user('admin-shared')
        clinics = [Clinic.objects.create(name=f'Clinic {i}', slug=f'clinic-{i}', status='ACTIVE') for i in (1, 2)]
        tokens = []
        for clinic in clinics:
            ClinicMembership.objects.create(user=admin, clinic=clinic, role='CLINIC_ADMIN', status='ACTIVE')
            _, token = create_invitation(actor=admin, clinic_id=clinic.pk, email='shared@example.com', role='DOCTOR', request_id=uuid.uuid4())
            tokens.append(token)
        barrier = threading.Barrier(2)

        def register(index):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                register_with_invitation(token=tokens[index], username=f'shared-{index}', password='Unique$Password987', request_id=uuid.uuid4())
                return 'created'
            except ValidationError:
                return 'denied'
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(register, (0, 1)))
        self.assertCountEqual(results, ['created', 'denied'])
        self.assertEqual(User.objects.filter(email__iexact='shared@example.com').count(), 1)

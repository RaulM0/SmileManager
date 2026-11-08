from unittest.mock import patch
from io import StringIO
from concurrent.futures import ThreadPoolExecutor
import threading

from django.contrib.auth.models import Permission, User
from django.core import mail
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import close_old_connections
from django.test import TransactionTestCase, override_settings, skipUnlessDBFeature
from django.urls import reverse
from rest_framework.test import APITestCase

from Usuarios.models import AuditEvent, Clinic, ClinicInvitation, ClinicMembership, PlatformAdmin
from api.serializers import SessionUserSerializer


@override_settings(TENANT_INVITATION_URL='https://example.test/app/invitations/accept')
class PlatformClinicTests(APITestCase):
    def setUp(self):
        self.platform = User.objects.create_user('platform-user', email='platform@example.test')
        self.role = PlatformAdmin.objects.create(user=self.platform, is_active=True)
        self.initial_admin = User.objects.create_user('initial-admin', email='initial@example.test')
        self.client.force_authenticate(self.platform)

    @staticmethod
    def payload():
        return {'name': 'Clínica Centro', 'slug': 'clinica-centro', 'status': 'ACTIVE', 'initial_admin_email': 'Initial@Example.test'}

    def test_platform_onboards_clinic_without_automatic_clinical_access(self):
        response = self.client.post(reverse('platform-clinics'), self.payload(), format='json')
        self.assertEqual(response.status_code, 201, response.data)
        clinic = Clinic.objects.get(pk=response.data['id'])
        self.assertEqual(clinic.status, 'ACTIVE')
        self.assertFalse(ClinicMembership.objects.filter(clinic=clinic).exists())
        invitation = ClinicInvitation.objects.get(clinic=clinic)
        self.assertEqual((invitation.email, invitation.role, invitation.status), ('initial@example.test', 'CLINIC_ADMIN', 'PENDING'))
        self.assertEqual(len(mail.outbox), 1)
        token = mail.outbox[0].body.split('#', 1)[1].strip()
        self.assertNotIn(token, str(response.data))
        self.assertTrue(AuditEvent.objects.filter(actor=self.platform, clinic=clinic, action='PLATFORM_CLINIC_CREATED').exists())
        self.assertEqual(self.client.get(reverse('backoffice-patients')).status_code, 403)
        self.assertEqual(self.client.get(reverse('tenant-patient-list'), HTTP_X_CLINIC_ID=str(clinic.pk)).status_code, 403)
        self.client.force_authenticate(self.initial_admin)
        accepted = self.client.post(reverse('clinic-invitation-resolve'), {'token': token, 'action': 'accept'}, format='json')
        self.assertEqual(accepted.status_code, 200)
        self.assertTrue(ClinicMembership.objects.filter(user=self.initial_admin, clinic=clinic, role='CLINIC_ADMIN', status='ACTIVE').exists())

    def test_staff_superuser_and_clinic_admin_are_not_platform_admins(self):
        root = User.objects.create_superuser('technical-root-platform', password='synthetic')
        root.user_permissions.add(Permission.objects.get(content_type__app_label='Usuarios', codename='access_system_backoffice'))
        clinic_admin = User.objects.create_user('local-admin')
        clinic = Clinic.objects.create(name='A', slug='local-clinic', status='ACTIVE')
        ClinicMembership.objects.create(user=clinic_admin, clinic=clinic, role='CLINIC_ADMIN', status='ACTIVE')
        for user in (root, clinic_admin):
            self.assertFalse(SessionUserSerializer(user).data['is_platform_admin'])
            self.client.force_authenticate(user)
            self.assertEqual(self.client.get(reverse('platform-clinics')).status_code, 403)
            self.assertEqual(self.client.post(reverse('platform-clinics'), self.payload(), format='json').status_code, 403)
        self.assertTrue(SessionUserSerializer(self.platform).data['is_platform_admin'])

    def test_status_transitions_and_immediate_platform_revocation(self):
        clinic = Clinic.objects.create(name='A', slug='state-clinic', status='INACTIVE')
        url = reverse('platform-clinic-status', args=[clinic.pk])
        self.assertEqual(self.client.post(url, {'status': 'SUSPENDED'}, format='json').status_code, 400)
        self.assertEqual(self.client.post(url, {'status': 'ACTIVE'}, format='json').status_code, 200)
        self.assertEqual(self.client.post(url, {'status': 'SUSPENDED'}, format='json').status_code, 200)
        self.assertTrue(AuditEvent.objects.filter(clinic=clinic, actor=self.platform, action='PLATFORM_CLINIC_SUSPENDED').exists())
        self.role.is_active = False
        self.role.save(update_fields=['is_active'])
        self.assertEqual(self.client.get(reverse('platform-clinics')).status_code, 403)

    @patch('api.tenant_views.send_mail', return_value=0)
    def test_delivery_failure_rolls_back_clinic_and_audit(self, _send):
        response = self.client.post(reverse('platform-clinics'), self.payload(), format='json')
        self.assertEqual(response.status_code, 503)
        self.assertFalse(Clinic.objects.exists())
        self.assertFalse(ClinicInvitation.objects.exists())
        self.assertFalse(AuditEvent.objects.filter(action='PLATFORM_CLINIC_CREATED').exists())

    def test_platform_can_revoke_and_replace_initial_invitation(self):
        created = self.client.post(reverse('platform-clinics'), self.payload(), format='json')
        clinic = Clinic.objects.get(pk=created.data['id'])
        first_id = created.data['initial_admin_invitation_id']
        list_url = reverse('platform-clinic-initial-admin', args=[clinic.pk])
        self.assertEqual(self.client.get(list_url).data['count'], 1)
        self.assertEqual(self.client.post(list_url, {'email': 'replacement@example.test'}, format='json').status_code, 409)
        revoke_url = reverse('platform-clinic-initial-admin-revoke', args=[clinic.pk, first_id])
        self.assertEqual(self.client.post(revoke_url).status_code, 204)
        replacement = self.client.post(list_url, {'email': 'replacement@example.test'}, format='json')
        self.assertEqual(replacement.status_code, 202)
        self.assertEqual(ClinicInvitation.objects.filter(clinic=clinic, status='PENDING').count(), 1)

    def test_legacy_backoffice_cannot_modify_platform_accounts(self):
        operator = User.objects.create_user('legacy-operator')
        operator.user_permissions.add(Permission.objects.get(content_type__app_label='Usuarios', codename='access_system_backoffice'))
        self.client.force_authenticate(operator)
        url = reverse('backoffice-user-action', args=[self.platform.pk, 'deactivate'])
        self.assertEqual(self.client.post(url).status_code, 409)
        self.platform.is_active = False
        self.platform.save(update_fields=['is_active'])
        url = reverse('backoffice-user-action', args=[self.platform.pk, 'activate'])
        self.assertEqual(self.client.post(url).status_code, 409)

    def test_platform_role_command_requires_explicit_assignment_and_defaults_to_dry_run(self):
        actor = User.objects.create_superuser('role-operator', password='synthetic')
        target = User.objects.create_user('role-target')
        options = {'actor_id': actor.pk, 'user_id': target.pk, 'action': 'grant'}
        with self.assertRaises(CommandError):
            call_command('manage_platform_admin', **options, stdout=StringIO())
        actor.user_permissions.add(Permission.objects.get(content_type__app_label='Usuarios', codename='manage_platform_roles'))
        output = StringIO()
        call_command('manage_platform_admin', **options, stdout=output)
        self.assertIn('DRY RUN', output.getvalue())
        self.assertFalse(PlatformAdmin.objects.filter(user=target).exists())
        call_command('manage_platform_admin', **options, apply=True, stdout=StringIO())
        self.assertTrue(PlatformAdmin.objects.filter(user=target, is_active=True).exists())
        self.assertTrue(AuditEvent.objects.filter(actor=actor, action='PLATFORM_ROLE_GRANTED', resource_id=str(target.pk)).exists())


@skipUnlessDBFeature('has_select_for_update')
class PlatformRoleConcurrencyTests(TransactionTestCase):
    def test_concurrent_revocations_keep_one_platform_administrator(self):
        actor = User.objects.create_user('platform-role-operator')
        actor.user_permissions.add(Permission.objects.get(content_type__app_label='Usuarios', codename='manage_platform_roles'))
        users = [User.objects.create_user('platform-one'), User.objects.create_user('platform-two')]
        for user in users:
            PlatformAdmin.objects.create(user=user, is_active=True)
        barrier = threading.Barrier(2)

        def revoke(index):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                call_command('manage_platform_admin', actor_id=actor.pk, user_id=users[index].pk,
                             action='revoke', apply=True, stdout=StringIO())
                return 'revoked'
            except CommandError:
                return 'denied'
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(revoke, (0, 1)))
        self.assertCountEqual(results, ['revoked', 'denied'])
        self.assertEqual(PlatformAdmin.objects.filter(is_active=True, user__is_active=True).count(), 1)

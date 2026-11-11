import base64
import time
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.management import call_command, CommandError
from io import StringIO
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken as UnboundRefreshToken

from Usuarios.models import AuthSession, MFACredential, MFAChallenge
from api.authentication import SessionRefreshToken
from api.services.mfa import totp
from api.throttles import MFAChallengeThrottle


class SessionAndMFATests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = Client(enforce_csrf_checks=True)
        self.user = User.objects.create_user('secure-user', password='Strong access phrase 459!', first_name='Persona', last_name='Prueba')
        self.admin = User.objects.create_user('secure-admin', password='Strong admin phrase 459!', is_staff=True)
        self.enterContext(patch('api.services.mfa.time.time', return_value=1700000000))

    def login(self, user=None):
        user = user or self.user
        password = 'Strong admin phrase 459!' if user.pk == self.admin.pk else 'Strong access phrase 459!'
        return self.client.post(reverse('api-login'), {'username': user.username, 'password': password}, content_type='application/json')

    def enroll(self):
        response = self.login(self.admin)
        self.assertTrue(response.json()['mfa_required'])
        self.assertNotIn('access', response.json())
        self.assertNotIn('smile_refresh', response.cookies)
        challenge = response.json()['challenge']
        setup = self.client.post(reverse('auth-mfa-setup'), {'challenge': challenge}, content_type='application/json')
        self.assertEqual(setup.status_code, 200, setup.content)
        secret = setup.json()['secret']
        response = self.client.post(reverse('auth-mfa-verify'), {'challenge': challenge, 'code': totp(secret, int(time.time()) // 30)}, content_type='application/json')
        self.assertEqual(response.status_code, 200, response.content)
        return secret, response.json(), challenge

    def test_totp_matches_rfc6238_sha1_vector(self):
        secret = base64.b32encode(b'12345678901234567890').decode()
        self.assertEqual(totp(secret, 59 // 30, digits=8), '94287082')
        self.assertEqual(totp(secret, 1111111109 // 30, digits=8), '07081804')

    def test_malformed_or_foreign_origin_cannot_issue_session_access(self):
        self.login()
        for origin in ('http://[', 'https://foreign.example.test'):
            self.assertEqual(self.client.get(reverse('api-session'), HTTP_ORIGIN=origin).status_code, 403)

    def test_admin_requires_mfa_and_seed_and_recovery_are_not_plaintext(self):
        secret, result, challenge = self.enroll()
        device = MFACredential.objects.get(user=self.admin)
        self.assertNotIn(secret, device.secret_ciphertext)
        self.assertEqual(len(result['recovery_codes']), 10)
        self.assertNotIn(result['recovery_codes'][0], str(device.recovery_hashes))
        session = AuthSession.objects.get(user=self.admin)
        self.assertTrue(session.mfa_verified)
        self.assertEqual(self.client.post(reverse('auth-mfa-verify'), {'challenge': challenge, 'code': result['recovery_codes'][0]}, content_type='application/json').status_code, 401)

    def test_replayed_totp_and_recovery_codes_are_rejected(self):
        secret, result, _ = self.enroll()
        challenge = self.login(self.admin).json()['challenge']
        response = self.client.post(reverse('auth-mfa-verify'), {'challenge': challenge, 'code': totp(secret, int(time.time()) // 30)}, content_type='application/json')
        self.assertEqual(response.status_code, 401)
        code = result['recovery_codes'][0]
        self.assertEqual(self.client.post(reverse('auth-mfa-verify'), {'challenge': challenge, 'code': code}, content_type='application/json').status_code, 200)
        another = self.login(self.admin).json()['challenge']
        self.assertEqual(self.client.post(reverse('auth-mfa-verify'), {'challenge': another, 'code': code}, content_type='application/json').status_code, 401)
        self.assertEqual(len(MFACredential.objects.get(user=self.admin).recovery_hashes), 9)

    def test_failed_challenge_attempts_are_persisted_and_limited(self):
        challenge = self.login(self.admin).json()['challenge']
        with patch.object(MFAChallengeThrottle, 'rate', '100/min', create=True):
            for _ in range(6):
                response = self.client.post(reverse('auth-mfa-verify'), {'challenge': challenge, 'code': 'invalid'}, content_type='application/json')
                self.assertEqual(response.status_code, 401)
        self.assertEqual(MFAChallenge.objects.get(user=self.admin).attempts, 5)
        self.assertFalse(AuthSession.objects.filter(user=self.admin).exists())

    def test_password_change_invalidates_pending_enrollment(self):
        challenge = self.login(self.admin).json()['challenge']
        self.admin.set_password('Replacement secret 829!')
        self.admin.save(update_fields=['password'])
        response = self.client.post(reverse('auth-mfa-setup'), {'challenge': challenge}, content_type='application/json')
        self.assertEqual(response.status_code, 401)

    def test_unbound_token_and_privileged_session_without_mfa_are_denied(self):
        for token in (UnboundRefreshToken.for_user(self.user).access_token, SessionRefreshToken.for_user(self.admin).access_token):
            response = self.client.get(reverse('api-dashboard'), HTTP_AUTHORIZATION=f'Bearer {token}')
            self.assertEqual(response.status_code, 401)

    def test_expiry_and_refresh_do_not_extend_absolute_lifetime(self):
        result = self.login().json()
        session = AuthSession.objects.get(user=self.user)
        expiration = session.expires_at
        self.assertEqual(self.client.post(reverse('api-refresh')).status_code, 200)
        session.refresh_from_db()
        self.assertEqual(session.expires_at, expiration)
        AuthSession.objects.filter(pk=session.pk).update(last_seen_at=timezone.now() - timedelta(minutes=31))
        self.assertEqual(self.client.get(reverse('api-dashboard'), HTTP_AUTHORIZATION=f"Bearer {result['access']}").status_code, 401)
        self.assertEqual(self.client.post(reverse('api-refresh')).status_code, 401)
        self.login()
        active = AuthSession.objects.filter(user=self.user).latest('created_at')
        AuthSession.objects.filter(pk=active.pk).update(expires_at=timezone.now() - timedelta(seconds=1))
        self.assertFalse(self.client.get(reverse('api-session')).json()['authenticated'])

    def test_revocation_is_immediate_and_cannot_target_another_user(self):
        result = self.login().json()
        current = AuthSession.objects.get(user=self.user)
        other = SessionRefreshToken.for_user(self.admin, mfa_verified=True)
        headers = {'HTTP_AUTHORIZATION': f"Bearer {result['access']}"}
        self.assertEqual(self.client.post(reverse('auth-session-revoke', args=[other['sid']]), **headers).status_code, 404)
        self.assertEqual(self.client.post(reverse('auth-session-revoke', args=[current.pk]), **headers).status_code, 204)
        self.assertEqual(self.client.get(reverse('api-dashboard'), **headers).status_code, 401)

    def test_sensitive_operation_requires_recent_reauthentication(self):
        result = self.login().json()
        session = AuthSession.objects.get(user=self.user)
        AuthSession.objects.filter(pk=session.pk).update(reauthenticated_at=timezone.now() - timedelta(minutes=6))
        headers = {'HTTP_AUTHORIZATION': f"Bearer {result['access']}"}
        response = self.client.patch(reverse('auth-own-profile'), {'first_name': 'Otro', 'last_name': 'Nombre'}, content_type='application/json', **headers)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()['code'], 'reauthentication_required')
        self.assertEqual(self.client.post(reverse('auth-reauthenticate'), {'password': 'Strong access phrase 459!', 'code': ''}, content_type='application/json', **headers).status_code, 200)
        self.assertEqual(self.client.patch(reverse('auth-own-profile'), {'first_name': 'Otro', 'last_name': 'Nombre'}, content_type='application/json', **headers).status_code, 200)

    def test_operator_reset_requires_confirmation_and_invalidates_old_credentials(self):
        self.admin.email = 'secure-admin@example.test'
        self.admin.save(update_fields=['email'])
        _, result, _ = self.enroll()
        with self.assertRaises(CommandError):
            call_command('reset_account_mfa', self.admin.username, confirm_username='wrong', reason='Autorización sintética de recuperación')
        self.assertTrue(MFACredential.objects.filter(user=self.admin).exists())
        call_command('reset_account_mfa', self.admin.username, confirm_username=self.admin.username,
                     reason='Autorización sintética de recuperación', stdout=StringIO())
        self.admin.refresh_from_db()
        self.assertFalse(self.admin.check_password('Strong admin phrase 459!'))
        self.assertFalse(MFACredential.objects.filter(user=self.admin).exists())
        self.assertEqual(self.client.get(reverse('api-dashboard'), HTTP_AUTHORIZATION=f"Bearer {result['access']}").status_code, 401)


    @override_settings(FEATURE_AI_ENABLED=True)
    def test_mfa_session_retains_ai_feature_metadata_after_integration(self):
        _, data, _ = self.enroll()
        self.assertTrue(data['user']['mfa_enabled'])
        self.assertTrue(data['user']['ai_globally_enabled'])
        response = self.client.get(reverse('api-session'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['user']['mfa_enabled'])
        self.assertTrue(response.json()['user']['ai_globally_enabled'])

from datetime import timedelta
from html.parser import HTMLParser
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from django.contrib.auth.models import Permission, User
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework_simplejwt.tokens import RefreshToken

from Usuarios.models import AuditEvent


@override_settings(FRONTEND_URL='https://testserver/app', DEFAULT_FROM_EMAIL='test@example.test', PASSWORD_RESET_TIMEOUT=1800)
class PasswordRecoveryTests(TestCase):
    def setUp(self):
        cache.clear()
        mail.get_connection()
        self.client = Client(enforce_csrf_checks=True)
        self.user = User.objects.create_user('doctor', email='doctor@example.test', password='original-password-123!')
        self.request_url = reverse('api-password-reset-request')
        self.confirm_url = reverse('api-password-reset-confirm')

    def request_link(self, email='doctor@example.test'):
        response = self.client.post(self.request_url, {'email': email}, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        link = next(line.split('continuar: ', 1)[1] for line in mail.outbox[-1].body.splitlines() if 'continuar: ' in line)
        fragment = parse_qs(urlsplit(link).fragment)
        return fragment['uid'][0], fragment['token'][0]

    def confirm(self, uid, token, password='Safe new passphrase 459!'):
        return self.client.post(self.confirm_url, {'uid': uid, 'token': token, 'new_password': password, 'confirm_password': password}, content_type='application/json')

    def test_email_has_branded_html_and_same_safe_link_as_plain_text(self):
        uid, token = self.request_link()
        message = mail.outbox[-1]
        self.assertEqual(len(message.alternatives), 1)
        html, mimetype = message.alternatives[0]
        self.assertEqual(mimetype, 'text/html')
        self.assertIn('SmileManager', html)
        self.assertIn('Restablecer contraseña', html)
        self.assertIn('30 minutos', html)
        self.assertIn('nunca te solicitará tu contraseña', html)
        class Links(HTMLParser):
            def __init__(self):
                super().__init__()
                self.hrefs = []
            def handle_starttag(self, tag, attrs):
                if tag == 'a':
                    self.hrefs.extend(value for name, value in attrs if name == 'href')
        parser = Links()
        parser.feed(html)
        expected = f'https://testserver/app/reset-password#uid={uid}&token={token}'
        self.assertIn(expected, parser.hrefs)
        self.assertIn(expected, message.body)
        self.assertNotIn('<img', html.lower())

    def test_html_template_escapes_url_attributes(self):
        html = render_to_string('api/emails/password_reset.html', {
            'reset_url': 'https://example.test/" onmouseover="malicious', 'expiry_minutes': 30,
        })
        self.assertNotIn('href="https://example.test/" onmouseover=', html)
        self.assertIn('&quot;', html)

    def test_generic_response_for_missing_inactive_and_ambiguous_accounts(self):
        inactive = User.objects.create_user('inactive', email='inactive@example.test', password='test', is_active=False)
        User.objects.create_user('duplicate1', email='dup@example.test', password='test')
        User.objects.create_user('duplicate2', email='DUP@example.test', password='test')
        results = [self.client.post(self.request_url, {'email': value}, content_type='application/json') for value in ('doctor@example.test', 'missing@example.test', inactive.email, 'dup@example.test')]
        self.assertTrue(all(result.status_code == 200 and result.json() == results[0].json() for result in results))
        self.assertEqual(len(mail.outbox), 1)
        self.assertNotIn('doctor@example.test', str(list(AuditEvent.objects.values())))
        self.assertFalse(self.client.post(self.request_url, {'email': 'bad'}, content_type='application/json').status_code == 200)

    def test_reset_single_use_and_revokes_refresh_without_changing_roles(self):
        permission = Permission.objects.get(content_type__app_label='Usuarios', codename='access_system_backoffice')
        self.user.user_permissions.add(permission)
        old_refresh = RefreshToken.for_user(self.user)
        old_access = str(old_refresh.access_token)
        uid, token = self.request_link()
        self.assertEqual(self.confirm(uid, token).status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)
        self.assertTrue(self.user.user_permissions.filter(pk=permission.pk).exists())
        self.assertFalse(self.user.is_staff)
        self.assertFalse(self.user.is_superuser)
        self.assertEqual(self.confirm(uid, token).status_code, 400)
        self.client.cookies['smile_refresh'] = str(old_refresh)
        self.assertEqual(self.client.post(reverse('api-refresh')).status_code, 401)
        self.assertFalse(self.client.get(reverse('api-session')).json()['authenticated'])
        # Existing access tokens are valid until expiry: five minutes by default.
        self.assertEqual(self.client.get(reverse('api-dashboard'), HTTP_AUTHORIZATION=f'Bearer {old_access}').status_code, 200)
        self.assertEqual(self.client.post(reverse('api-login'), {'username': 'doctor', 'password': 'original-password-123!'}, content_type='application/json').status_code, 400)
        self.assertEqual(self.client.post(reverse('api-login'), {'username': 'doctor', 'password': 'Safe new passphrase 459!'}, content_type='application/json').status_code, 200)
        event = AuditEvent.objects.get(action='PASSWORD_RESET_COMPLETED')
        self.assertIsNone(event.actor_id)
        self.assertEqual(event.resource_id, str(self.user.pk))
        self.assertNotIn(token, str(list(AuditEvent.objects.values())))

    def test_invalid_expired_inactive_and_mismatch(self):
        uid, token = self.request_link()
        self.assertEqual(self.confirm(uid, token + 'x').status_code, 400)
        self.assertEqual(self.confirm('@@@', token).status_code, 400)
        other = User.objects.create_user('other', email='other@example.test', password='test')
        self.assertEqual(self.confirm(urlsafe_base64_encode(force_bytes(other.pk)), token).status_code, 400)
        future = default_token_generator._now() + timedelta(seconds=1801)
        with patch.object(default_token_generator, '_now', return_value=future):
            self.assertEqual(self.confirm(uid, token).status_code, 400)
        mismatch = self.client.post(self.confirm_url, {'uid': uid, 'token': token, 'new_password': 'Safe passphrase 123!', 'confirm_password': 'different'}, content_type='application/json')
        self.assertEqual(mismatch.status_code, 400)
        self.assertEqual(self.confirm(uid, token, '123').status_code, 400)
        self.user.is_active = False
        self.user.save(update_fields=['is_active'])
        self.assertEqual(self.confirm(uid, token).status_code, 400)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)

    def test_repeated_requests_are_invalidated_together(self):
        uid, first = self.request_link()
        _, second = self.request_link()
        self.assertEqual(self.confirm(uid, second).status_code, 200)
        self.assertEqual(self.confirm(uid, first).status_code, 400)

    def test_rate_limit_and_cross_origin(self):
        with patch('api.throttles.PasswordResetIPThrottle.get_rate', return_value='2/min'), patch('api.throttles.PasswordResetAccountThrottle.get_rate', return_value='50/min'):
            for email in ('a@example.test', 'b@example.test'):
                self.assertEqual(self.client.post(self.request_url, {'email': email}, content_type='application/json').status_code, 200)
            self.assertEqual(self.client.post(self.request_url, {'email': 'c@example.test'}, content_type='application/json').status_code, 429)
        cache.clear()
        self.assertEqual(self.client.post(self.request_url, {'email': 'a@example.test'}, content_type='application/json', HTTP_ORIGIN='https://evil.example').status_code, 403)

    def test_account_limit_applies_equally_to_nonexistent_and_existing_email(self):
        with patch('api.throttles.PasswordResetIPThrottle.get_rate', return_value='50/min'), patch('api.throttles.PasswordResetAccountThrottle.get_rate', return_value='1/min'):
            for email in ('doctor@example.test', 'missing@example.test'):
                self.assertEqual(self.client.post(self.request_url, {'email': email}, content_type='application/json').status_code, 200)
                self.assertEqual(self.client.post(self.request_url, {'email': email.upper()}, content_type='application/json').status_code, 429)

    def test_confirmation_limit_is_independent(self):
        uid, token = self.request_link()
        with patch('api.throttles.PasswordResetConfirmThrottle.get_rate', return_value='1/min'):
            self.assertEqual(self.confirm(uid, token + 'x').status_code, 400)
            self.assertEqual(self.confirm(uid, token).status_code, 429)

    def test_smtp_error_is_generic_and_never_logged_with_token(self):
        with patch('api.services.password_recovery.EmailMultiAlternatives.send', side_effect=RuntimeError('synthetic secret')), self.assertLogs('api.services.password_recovery', level='WARNING') as logs:
            response = self.client.post(self.request_url, {'email': 'doctor@example.test'}, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('synthetic secret', str(logs.output))
        self.assertNotIn('doctor@example.test', str(logs.output))

    def test_no_email_unusable_password_and_invalid_frontend(self):
        self.user.set_unusable_password()
        self.user.save(update_fields=['password'])
        self.client.post(self.request_url, {'email': 'doctor@example.test'}, content_type='application/json')
        self.assertEqual(len(mail.outbox), 0)
        self.user.set_password('old secure password!')
        self.user.save(update_fields=['password'])
        with override_settings(FRONTEND_URL='https://evil.example@trusted.example'):
            self.client.post(self.request_url, {'email': 'doctor@example.test'}, content_type='application/json')
        self.assertEqual(len(mail.outbox), 0)

    def test_methods_origin_and_invalid_inputs_do_not_change_credentials(self):
        self.assertEqual(self.client.get(self.confirm_url).status_code, 405)
        self.assertEqual(self.client.get(self.request_url).status_code, 405)
        self.assertEqual(self.client.post(self.request_url, {'email': ''}, content_type='application/json').status_code, 400)
        uid, token = self.request_link()
        rejected = self.client.post(self.confirm_url, {'uid': uid, 'token': token, 'new_password': 'Valid new password 459!', 'confirm_password': 'Valid new password 459!'}, content_type='application/json', HTTP_ORIGIN='https://evil.example')
        self.assertEqual(rejected.status_code, 403)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('original-password-123!'))

    def test_official_password_validators_reject_weak_values(self):
        uid, token = self.request_link()
        for value in ('short', '1234567890', 'password', 'doctor12'):
            response = self.confirm(uid, token, value)
            self.assertEqual(response.status_code, 400)
            self.assertIn('new_password', response.json())
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('original-password-123!'))

    def test_audit_failure_rolls_back_password_and_refresh_revocation(self):
        uid, token = self.request_link()
        refresh = str(RefreshToken.for_user(self.user))
        self.client.raise_request_exception = False
        with patch('api.services.password_recovery.AuditEvent.objects.create', side_effect=RuntimeError('synthetic')):
            response = self.confirm(uid, token)
        self.assertEqual(response.status_code, 500)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('original-password-123!'))
        self.client.cookies['smile_refresh'] = refresh
        self.assertEqual(self.client.post(reverse('api-refresh')).status_code, 200)

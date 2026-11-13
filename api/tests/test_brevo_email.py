import json
import os
import subprocess
import sys
from unittest.mock import patch

from django.core.mail import EmailMultiAlternatives, get_connection
from django.test import SimpleTestCase, override_settings
import requests


@override_settings(
    EMAIL_BACKEND='anymail.backends.brevo.EmailBackend',
    ANYMAIL={'BREVO_API_KEY': 'synthetic-api-key', 'REQUESTS_TIMEOUT': (5, 10)},
    DEFAULT_FROM_EMAIL='SmileManager <sender@example.test>',
)
class BrevoEmailTests(SimpleTestCase):
    def response(self, code, body):
        response = requests.Response()
        response.status_code = code
        response._content = json.dumps(body).encode()
        response.headers['Content-Type'] = 'application/json'
        response.encoding = 'utf-8'
        return response

    @patch('requests.Session.request')
    def test_html_text_and_attachment_use_https_api(self, request):
        request.return_value = self.response(201, {'messageId': '<synthetic@example.test>'})
        message = EmailMultiAlternatives('Prueba', 'Contenido de prueba', None, ['recipient@example.test'])
        message.attach_alternative('<p>Contenido de prueba</p>', 'text/html')
        message.attach('synthetic.pdf', b'%PDF-synthetic', 'application/pdf')
        self.assertEqual(message.send(), 1)
        args = request.call_args.kwargs
        self.assertEqual(args['url'], 'https://api.brevo.com/v3/smtp/email')
        self.assertEqual(args['headers']['api-key'], 'synthetic-api-key')
        payload = json.loads(args['data'])
        self.assertEqual(payload['textContent'], 'Contenido de prueba')
        self.assertEqual(payload['htmlContent'], '<p>Contenido de prueba</p>')
        self.assertEqual(payload['sender']['email'], 'sender@example.test')
        self.assertEqual(payload['attachment'][0]['name'], 'synthetic.pdf')
        self.assertEqual(args['timeout'], (5, 10))

    @patch('requests.Session.request')
    def test_rejection_is_not_reported_as_sent_and_is_not_retried(self, request):
        from anymail.exceptions import AnymailAPIError
        request.return_value = self.response(400, {'code': 'invalid_parameter', 'message': 'Rejected'})
        message = EmailMultiAlternatives('Prueba', 'Texto', None, ['recipient@example.test'])
        with self.assertRaises(AnymailAPIError):
            message.send()
        request.assert_called_once()

    @patch('requests.Session.request')
    def test_transport_failure_propagates_or_respects_fail_silently(self, request):
        from anymail.exceptions import AnymailRequestsAPIError
        request.side_effect = requests.Timeout('synthetic timeout')
        message = EmailMultiAlternatives('Prueba', 'Texto', None, ['recipient@example.test'])
        with self.assertRaises(AnymailRequestsAPIError):
            message.send()
        message.connection = get_connection(fail_silently=True)
        self.assertEqual(message.send(), 0)


class BrevoSettingsTests(SimpleTestCase):
    def settings_for(self, **values):
        environment = {
            **os.environ,
            'DJANGO_SETTINGS_MODULE': 'SmileManager.settings_local',
            'PYTHON_DOTENV_DISABLED': '1',
            'EMAIL_PROVIDER': 'brevo',
            'BREVO_API_KEY': 'synthetic-api-key',
            'DEFAULT_FROM_EMAIL': 'sender@example.test',
            'DEV_EMAIL_DELIVERY': 'brevo',
            **values,
        }
        return subprocess.run(
            [sys.executable, '-B', '-c', 'from django.conf import settings; print(settings.EMAIL_BACKEND)'],
            env=environment, capture_output=True, text=True, timeout=30,
        )

    def test_explicit_local_opt_in_uses_brevo(self):
        result = self.settings_for()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), 'anymail.backends.brevo.EmailBackend')

    def test_missing_credentials_and_unknown_provider_fail_closed(self):
        for values in ({'BREVO_API_KEY': ''}, {'DEFAULT_FROM_EMAIL': ''}, {'EMAIL_PROVIDER': 'unknown'}):
            with self.subTest(values=values):
                self.assertNotEqual(self.settings_for(**values).returncode, 0)


class VerifyEmailCommandTests(SimpleTestCase):
    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_command_refuses_a_backend_that_cannot_prove_brevo_delivery(self):
        from django.core.management import call_command
        from django.core.management.base import CommandError
        with self.assertRaises(CommandError):
            call_command('verify_email', to='operator@example.test')

    @override_settings(EMAIL_BACKEND='anymail.backends.brevo.EmailBackend')
    @patch('api.management.commands.verify_email.send_mail', side_effect=RuntimeError('private-api-key'))
    def test_command_failure_does_not_disclose_provider_exception(self, send):
        from django.core.management import call_command
        from django.core.management.base import CommandError
        with self.assertRaises(CommandError) as error:
            call_command('verify_email', to='operator@example.test')
        self.assertNotIn('private-api-key', str(error.exception))

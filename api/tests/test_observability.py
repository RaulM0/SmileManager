import json
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class LoggingTests(TestCase):
    def test_no_payload_cookie_or_url_identifiers_in_access_log(self):
        user = User.objects.create_user('synthetic-logger')
        self.client.force_login(user)
        with self.assertLogs('smile.access', level='INFO') as captured:
            response = self.client.get(reverse('api-session') + '?secret=private')
        event = json.loads(captured.records[0].getMessage())
        self.assertEqual(event['request_id'], response['X-Request-ID'])
        self.assertEqual(event['endpoint'], 'api-session')
        self.assertNotIn('private', captured.output[0])

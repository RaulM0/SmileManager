from unittest.mock import patch
from django.db import OperationalError
from django.test import TestCase
from django.urls import reverse


class HealthTests(TestCase):
    def test_live_and_ready_without_authentication(self):
        self.assertEqual(self.client.get(reverse('health-live')).json(), {'status': 'ok'})
        self.assertEqual(self.client.get(reverse('health-ready')).status_code, 200)
        self.assertEqual(self.client.get('/health').status_code, 200)
        self.assertEqual(self.client.get('/health/ready').status_code, 200)
        self.assertEqual(self.client.post(reverse('health-live')).status_code, 405)

    def test_readiness_hides_database_error(self):
        with patch('api.health.connection.cursor', side_effect=OperationalError('internal secret path')):
            response = self.client.get(reverse('health-ready'))
        self.assertEqual(response.status_code, 503)
        self.assertNotIn('internal', response.content.decode())

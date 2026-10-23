from datetime import timedelta

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from Citas.models import Cita
from Pacientes.models import Paciente


class AuthApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='doctor', password='secret123')
        self.client = Client(enforce_csrf_checks=True)

    def csrf_token(self):
        response = self.client.get(reverse('api-session'))
        self.assertEqual(response.status_code, 200)
        return response.json()['csrf_token']

    def test_session_is_public_and_sets_csrf_cookie(self):
        response = self.client.get(reverse('api-session'))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['authenticated'])
        self.assertIn('csrftoken', response.cookies)

    def test_login_requires_csrf_and_returns_user_profile(self):
        response = self.client.post(
            reverse('api-login'),
            {'username': 'doctor', 'password': 'secret123'},
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 403)

        token = self.csrf_token()
        response = self.client.post(
            reverse('api-login'),
            {'username': 'doctor', 'password': 'secret123'},
            content_type='application/json',
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['user']['username'], 'doctor')
        self.assertIn('profile', response.json()['user'])
        self.assertIn('csrf_token', response.json())
        self.assertNotEqual(response.json()['csrf_token'], token)

    def test_invalid_credentials_preserve_legacy_message(self):
        token = self.csrf_token()
        response = self.client.post(
            reverse('api-login'),
            {'username': 'doctor', 'password': 'wrong'},
            content_type='application/json',
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['detail'], 'Usuario o contraseña incorrectos')

    def test_logout_invalidates_session(self):
        self.client.force_login(self.user)
        token = self.csrf_token()
        response = self.client.post(reverse('api-logout'), HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(self.client.get(reverse('api-session')).json()['authenticated'])


class DashboardApiTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='owner', password='secret123')
        self.other = User.objects.create_user(username='other', password='secret123')
        self.patient = Paciente.objects.create(
            nombre='ANA', appat='LOPEZ', apmat='DIAZ',
            fecha_nacimiento='1990-01-01', genero='F', telefono='1111111111',
            email='ANA@EXAMPLE.COM', medico=self.owner,
        )
        other_patient = Paciente.objects.create(
            nombre='OTRO', appat='PACIENTE', apmat='DOS',
            fecha_nacimiento='1990-01-01', genero='M', telefono='2222222222',
            email='OTRO@EXAMPLE.COM', medico=self.other,
        )
        today = timezone.localdate()
        Cita.objects.create(paciente=self.patient, fecha=today, hora='10:00', motivo='HOY')
        Cita.objects.create(paciente=self.patient, fecha=today + timedelta(days=1), hora='11:00', motivo='FUTURA')
        Cita.objects.create(paciente=other_patient, fecha=today, hora='12:00', motivo='AJENA')

    def test_requires_authentication(self):
        self.assertEqual(self.client.get(reverse('api-dashboard')).status_code, 403)

    def test_matches_legacy_counts_and_owner_scope(self):
        self.client.force_login(self.owner)
        payload = self.client.get(reverse('api-dashboard')).json()
        self.assertEqual(payload['patient_count'], 1)
        self.assertEqual([item['motivo'] for item in payload['today']], ['HOY'])
        self.assertEqual([item['motivo'] for item in payload['upcoming']], ['FUTURA'])

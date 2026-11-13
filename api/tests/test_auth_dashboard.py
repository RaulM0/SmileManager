from datetime import timedelta

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from api.authentication import SessionRefreshToken as RefreshToken

from Citas.models import Cita
from Pacientes.models import ImagenesClinicas, Paciente
from tempfile import TemporaryDirectory


class AuthApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='doctor', password='secret123')
        self.client = Client(enforce_csrf_checks=True)

    def test_session_is_public_without_csrf_cookie(self):
        response = self.client.get(reverse('api-session'))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['authenticated'])
        self.assertNotIn('csrf_token', response.json())

    def test_login_issues_bearer_token_without_csrf(self):
        response = self.client.post(
            reverse('api-login'),
            {'username': 'doctor', 'password': 'secret123'},
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['user']['username'], 'doctor')
        self.assertIn('profile', response.json()['user'])
        self.assertIn('access', response.json())
        self.assertNotIn('csrf_token', response.json())
        self.assertTrue(response.cookies['smile_refresh']['httponly'])
        self.assertNotIn('sessionid', response.cookies)

    def test_invalid_credentials_preserve_legacy_message(self):
        response = self.client.post(
            reverse('api-login'),
            {'username': 'doctor', 'password': 'wrong'},
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['detail'], 'Usuario o contraseña incorrectos')

    def test_refresh_rotates_and_logout_blacklists_token(self):
        self.client.post(reverse('api-login'), {'username': 'doctor', 'password': 'secret123'}, content_type='application/json')
        old_refresh = self.client.cookies['smile_refresh'].value
        refreshed = self.client.post(reverse('api-refresh'))
        self.assertEqual(refreshed.status_code, 200)
        self.assertIn('access', refreshed.json())
        self.assertNotEqual(self.client.cookies['smile_refresh'].value, old_refresh)
        response = self.client.post(reverse('api-logout'))
        self.assertEqual(response.status_code, 204)
        self.assertFalse(self.client.get(reverse('api-session')).json()['authenticated'])
        self.assertEqual(self.client.post(reverse('api-refresh')).status_code, 401)

    def test_session_cookie_cannot_authorize_api(self):
        self.client.force_login(self.user)
        self.assertIn(self.client.get(reverse('api-dashboard')).status_code, (401, 403))

    def test_refresh_rejects_foreign_origin(self):
        self.client.post(reverse('api-login'), {'username': 'doctor', 'password': 'secret123'}, content_type='application/json')
        response = self.client.post(reverse('api-refresh'), HTTP_ORIGIN='https://untrusted.example')
        self.assertEqual(response.status_code, 403)

    def test_clinical_file_requires_bearer_and_owner(self):
        other = User.objects.create_user(username='another', password='secret123')
        patient = Paciente.objects.create(
            nombre='ANA', appat='LOPEZ', apmat='DIAZ', fecha_nacimiento='1990-01-01',
            genero='F', telefono='1111111111', email='ANA@EXAMPLE.COM', medico=self.user,
        )
        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            image = ImagenesClinicas.objects.create(
                paciente=patient, medico=self.user, tipo_imagen='Radiografía',
                imagen=SimpleUploadedFile('radiograph.png', b'clinical-image'),
            )
            url = reverse('api-clinical-image-file', args=[image.id])
            self.assertEqual(self.client.get(url).status_code, 401)
            other_token = RefreshToken.for_user(other).access_token
            self.assertEqual(self.client.get(url, HTTP_AUTHORIZATION=f'Bearer {other_token}').status_code, 404)
            owner_token = RefreshToken.for_user(self.user).access_token
            response = self.client.get(url, HTTP_AUTHORIZATION=f'Bearer {owner_token}')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(b''.join(response.streaming_content), b'clinical-image')


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
        self.assertEqual(self.client.get(reverse('api-dashboard')).status_code, 401)

    def test_matches_legacy_counts_and_owner_scope(self):
        token = RefreshToken.for_user(self.owner).access_token
        payload = self.client.get(reverse('api-dashboard'), HTTP_AUTHORIZATION=f'Bearer {token}').json()
        self.assertEqual(payload['patient_count'], 1)
        self.assertEqual([item['motivo'] for item in payload['today']], ['HOY'])
        self.assertEqual([item['motivo'] for item in payload['upcoming']], ['FUTURA'])

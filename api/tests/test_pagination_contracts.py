from datetime import timedelta
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from Citas.models import Cita
from Pacientes.models import Consulta, ImagenesClinicas, Paciente


@override_settings(CLINICAL_PAGE_SIZE=2, CLINICAL_MAX_PAGE_SIZE=3, APPOINTMENT_MAX_RANGE_DAYS=62)
class PaginationContractTests(TestCase):
    def setUp(self):
        self.a = User.objects.create_user('page-a')
        self.b = User.objects.create_user('page-b')
        self.patient = Paciente.objects.create(nombre='A', appat='A', apmat='A', fecha_nacimiento='1990-01-01', genero='F', telefono='1111111111', email='a@example.test', medico=self.a)
        self.foreign = Paciente.objects.create(nombre='B', appat='B', apmat='B', fecha_nacimiento='1990-01-01', genero='F', telefono='2222222222', email='b@example.test', medico=self.b)
        self.client = APIClient()
        self.client.force_authenticate(self.a)
        for _ in range(5):
            consultation = Consulta.objects.create(paciente=self.patient, medico=self.a, fecha_consulta=timezone.now(), motivo_consulta='x')
            ImagenesClinicas.objects.create(paciente=self.patient, medico=self.a, consulta=consultation, tipo_imagen='RX', imagen='synthetic/x.png')
            Cita.objects.create(paciente=self.patient, fecha='2026-10-15', hora='10:00', motivo='x')
        Cita.objects.create(paciente=self.foreign, fecha='2026-10-15', hora='10:00', motivo='foreign')

    def test_pages_stable_bounded_and_owned(self):
        for url in (reverse('api-consultations', args=[self.patient.pk]), reverse('api-clinical-images', args=[self.patient.pk]), reverse('api-appointment-list')):
            first = self.client.get(url, {'page_size': 100000})
            self.assertEqual(first.status_code, 200)
            self.assertEqual(first.data['count'], 5)
            self.assertEqual(len(first.data['results']), 3)
            second = self.client.get(url, {'page_size': 3, 'page': 2})
            self.assertEqual(len(second.data['results']), 2)
            self.assertFalse(set(r['id'] for r in first.data['results']) & set(r['id'] for r in second.data['results']))
        self.assertEqual(self.client.get(reverse('api-consultations', args=[self.foreign.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse('api-clinical-images', args=[self.foreign.pk])).status_code, 404)

    def test_calendar_range_validation(self):
        url = reverse('api-appointment-list')
        self.assertEqual(self.client.get(url, {'from': '2026-10-01', 'to': '2026-10-31'}).data['count'], 5)
        self.assertEqual(self.client.get(url, {'from': '2026-11-01', 'to': '2026-11-30'}).data['count'], 0)
        for params in ({'from': '2026-10-01'}, {'from': 'invalid', 'to': '2026-10-31'}, {'from': '2026-12-31', 'to': '2026-01-01'}, {'from': '1900-01-01', 'to': '2100-01-01'}):
            self.assertEqual(self.client.get(url, params).status_code, 400)

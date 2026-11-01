from datetime import timedelta

from django.contrib.auth.models import User
from django.db import connection
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from Citas.models import Cita
from Pacientes.models import Consulta, ImagenesClinicas, Paciente


class QueryRegressionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('performance-test')
        self.patient = Paciente.objects.create(nombre='Synthetic', appat='A', apmat='B', fecha_nacimiento='1990-01-01', genero='F', telefono='1234567890', email='synthetic@example.test', medico=self.user)
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.consultations = [Consulta.objects.create(paciente=self.patient, medico=self.user, fecha_consulta=timezone.now(), motivo_consulta='Synthetic') for _ in range(10)]
        ImagenesClinicas.objects.bulk_create([ImagenesClinicas(paciente=self.patient, medico=self.user, consulta=c, tipo_imagen='RX', imagen='synthetic/test.png') for c in self.consultations])

    def test_consultations_and_images_do_not_add_a_query_per_row(self):
        for name in ('api-consultations', 'api-clinical-images'):
            with self.subTest(endpoint=name), CaptureQueriesContext(connection) as queries:
                response = self.client.get(reverse(name, args=[self.patient.pk]))
                self.assertEqual(response.status_code, 200)
                self.assertLessEqual(len(queries), 4)

    def test_dashboard_is_bounded_and_count_is_not_truncated(self):
        Cita.objects.bulk_create([Cita(paciente=self.patient, fecha=timezone.localdate(), hora='10:00', motivo='Synthetic') for _ in range(55)])
        Cita.objects.bulk_create([Cita(paciente=self.patient, fecha=timezone.localdate()+timedelta(days=1), hora='10:00', motivo='Synthetic') for _ in range(55)])
        response = self.client.get(reverse('api-dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['today_count'], 55)
        self.assertEqual(len(response.data['today']), 50)
        self.assertEqual(len(response.data['upcoming']), 50)

    @override_settings(EXPORT_MAX_ROWS=1)
    def test_export_over_limit_is_rejected(self):
        Paciente.objects.create(nombre='Other', appat='A', apmat='B', fecha_nacimiento='1990-01-01', genero='F', telefono='9999999999', email='other@example.test', medico=self.user)
        response = self.client.get(reverse('api-export-patients'))
        self.assertEqual(response.status_code, 413)
        self.assertIn('límite', response.json()['detail'])

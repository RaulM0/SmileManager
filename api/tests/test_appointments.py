from datetime import timedelta

from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from Citas.models import Cita
from Pacientes.models import Paciente


class AppointmentApiTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='owner', password='secret123')
        self.other = User.objects.create_user(username='other', password='secret123')
        self.patient = self.patient_for(self.owner, '1111111111', 'A@EXAMPLE.COM')
        self.foreign = self.patient_for(self.other, '2222222222', 'B@EXAMPLE.COM')
        self.client.force_authenticate(self.owner)

    def patient_for(self, owner, phone, email):
        return Paciente.objects.create(
            nombre='ANA', appat='LOPEZ', apmat='DIAZ', fecha_nacimiento='1990-01-01',
            genero='F', telefono=phone, email=email, medico=owner,
        )

    def payload(self, **overrides):
        data = {'paciente_id': self.patient.id, 'fecha': str(timezone.localdate() + timedelta(days=1)), 'hora': '10:00', 'motivo': 'Control', 'estatus': 'P', 'observaciones': 'Ninguna'}
        data.update(overrides)
        return data

    def test_create_and_update_preserve_schedule_rules(self):
        response = self.client.post(reverse('api-appointment-list'), self.payload(), format='json')
        self.assertEqual(response.status_code, 201)
        invalid = self.client.patch(reverse('api-appointment-detail', args=[response.data['id']]), {'hora':'07:59'}, format='json')
        self.assertEqual(invalid.status_code, 400)
        self.assertEqual(str(invalid.data['hora'][0]), 'La hora debe estar entre las 08:00 y las 20:00.')

    def test_rejects_past_date_and_foreign_patient(self):
        past = self.client.post(reverse('api-appointment-list'), self.payload(fecha=str(timezone.localdate()-timedelta(days=1))), format='json')
        self.assertEqual(past.status_code, 400)
        foreign = self.client.post(reverse('api-appointment-list'), self.payload(paciente_id=self.foreign.id), format='json')
        self.assertEqual(foreign.status_code, 400)

    def test_list_search_status_and_actions_are_owner_scoped(self):
        own = Cita.objects.create(paciente=self.patient, fecha=timezone.localdate()+timedelta(days=1), hora='10:00', motivo='Control')
        Cita.objects.create(paciente=self.foreign, fecha=timezone.localdate()+timedelta(days=1), hora='11:00', motivo='Ajena')
        listing = self.client.get(reverse('api-appointment-list'), {'search':'ANA','status':'P'})
        self.assertEqual([item['id'] for item in listing.data], [own.id])
        completed = self.client.post(reverse('api-appointment-complete', args=[own.id]))
        self.assertEqual(completed.data['estatus'], 'C')
        cancelled = self.client.post(reverse('api-appointment-cancel', args=[own.id]))
        self.assertEqual(cancelled.data['estatus'], 'A')

    def test_foreign_detail_is_hidden(self):
        foreign = Cita.objects.create(paciente=self.foreign, fecha=timezone.localdate(), hora='10:00', motivo='Ajena')
        self.assertEqual(self.client.get(reverse('api-appointment-detail', args=[foreign.id])).status_code, 404)

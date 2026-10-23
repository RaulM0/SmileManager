from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase

from Pacientes.models import AntescedentesMedicos, Paciente


class ClinicalRecordApiTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='owner', password='secret123')
        self.other = User.objects.create_user(username='other', password='secret123')
        self.patient = Paciente.objects.create(
            nombre='ANA', appat='LOPEZ', apmat='DIAZ', fecha_nacimiento='1990-01-01',
            genero='F', telefono='1111111111', email='ANA@EXAMPLE.COM', medico=self.owner,
        )
        self.client.force_authenticate(self.owner)

    def test_get_history_preserves_legacy_get_or_create(self):
        response = self.client.get(reverse('api-medical-history', args=[self.patient.id]))
        self.assertEqual(response.status_code, 200)
        history = AntescedentesMedicos.objects.get(paciente=self.patient)
        self.assertEqual(history.medico, self.owner)
        self.assertFalse(response.data['problemas_cardiacos'])

    def test_update_history_preserves_boolean_and_text_fields(self):
        response = self.client.put(
            reverse('api-medical-history', args=[self.patient.id]),
            {'problemas_cardiacos': True, 'alergias': 'Penicilina'}, format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['problemas_cardiacos'])
        self.assertEqual(response.data['alergias'], 'Penicilina')

    def test_foreign_patient_history_is_hidden(self):
        foreign = Paciente.objects.create(
            nombre='B', appat='B', apmat='B', fecha_nacimiento='1990-01-01', genero='M',
            telefono='2222222222', email='B@EXAMPLE.COM', medico=self.other,
        )
        self.assertEqual(self.client.get(reverse('api-medical-history', args=[foreign.id])).status_code, 404)

    def test_create_consultation_normalizes_and_applies_defaults(self):
        response = self.client.post(
            reverse('api-consultations', args=[self.patient.id]),
            {'motivo_consulta': 'dolor', 'diagnostico': 'caries'}, format='json',
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['motivo_consulta'], 'DOLOR')
        self.assertEqual(response.data['diagnostico'], 'CARIES')
        self.assertEqual(response.data['tratamiento'], 'NINGUNO')
        self.assertEqual(response.data['observaciones'], 'NINGUNA')

    def test_history_and_detail_are_owner_scoped(self):
        created = self.client.post(
            reverse('api-consultations', args=[self.patient.id]),
            {'motivo_consulta': 'control'}, format='json',
        ).data
        listing = self.client.get(reverse('api-consultations', args=[self.patient.id]))
        self.assertEqual([item['id'] for item in listing.data], [created['id']])
        detail = self.client.get(reverse('api-consultation-detail', args=[created['id']]))
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.data['paciente']['id'], self.patient.id)

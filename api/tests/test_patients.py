from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase

from Pacientes.models import Paciente


def patient_data(**overrides):
    data = {
        'nombre': 'Ana', 'appat': 'López', 'apmat': 'Díaz',
        'fecha_nacimiento': '1990-01-01', 'genero': 'F',
        'telefono': '1111111111', 'email': 'ana@example.com', 'estatus': 'A',
    }
    data.update(overrides)
    return data


class PatientApiTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='owner', password='secret123')
        self.other = User.objects.create_user(username='other', password='secret123')
        self.client.force_authenticate(self.owner)

    def create(self, owner=None, **overrides):
        data = patient_data(**overrides)
        for field in ('nombre', 'appat', 'apmat', 'email'):
            data[field] = data[field].upper()
        return Paciente.objects.create(medico=owner or self.owner, **data)

    def test_create_preserves_legacy_normalization_and_owner(self):
        response = self.client.post(reverse('api-patient-list'), patient_data(), format='json')
        self.assertEqual(response.status_code, 201)
        patient = Paciente.objects.get(pk=response.data['id'])
        self.assertEqual(patient.nombre, 'ANA')
        self.assertEqual(patient.email, 'ANA@EXAMPLE.COM')
        self.assertEqual(patient.medico, self.owner)

    def test_create_preserves_duplicate_messages_per_doctor(self):
        self.create()
        response = self.client.post(reverse('api-patient-list'), patient_data(), format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(str(response.data['telefono'][0]), 'El teléfono ya está registrado para tu consultorio.')
        self.assertEqual(str(response.data['email'][0]), 'El email ya está registrado para tu consultorio.')

    def test_list_search_and_detail_are_owner_scoped(self):
        own = self.create()
        self.create(owner=self.other, telefono='2222222222', email='other@example.com')
        response = self.client.get(reverse('api-patient-list'), {'search': 'López'})
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], own.id)
        self.assertEqual(
            self.client.get(reverse('api-patient-detail', args=[own.id])).status_code, 200,
        )

    def test_cannot_access_another_doctors_patient(self):
        foreign = self.create(owner=self.other)
        self.assertEqual(
            self.client.get(reverse('api-patient-detail', args=[foreign.id])).status_code, 404,
        )

    def test_update_normalizes_and_validates_uniqueness(self):
        patient = self.create()
        response = self.client.patch(
            reverse('api-patient-detail', args=[patient.id]),
            {'nombre': 'Beatriz', 'email': 'beatriz@example.com'}, format='json',
        )
        self.assertEqual(response.status_code, 200)
        patient.refresh_from_db()
        self.assertEqual(patient.nombre, 'BEATRIZ')
        self.assertEqual(patient.email, 'BEATRIZ@EXAMPLE.COM')

    def test_deactivate_is_logical_delete(self):
        patient = self.create()
        response = self.client.post(reverse('api-patient-deactivate', args=[patient.id]))
        self.assertEqual(response.status_code, 200)
        patient.refresh_from_db()
        self.assertEqual(patient.estatus, 'I')

    def test_autocomplete_matches_legacy_name_only_and_limit(self):
        own = self.create(nombre='Ana')
        response = self.client.get(reverse('api-patient-autocomplete'), {'term': 'an'})
        self.assertEqual(response.data, {'results': [{'id': own.id, 'text': 'ANA LÓPEZ DÍAZ'}]})

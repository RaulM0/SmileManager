from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase

from Pacientes.models import Odontograma, Paciente


class OdontogramApiTests(APITestCase):
    def setUp(self):
        self.owner=User.objects.create_user(username='owner',password='secret123')
        self.other=User.objects.create_user(username='other',password='secret123')
        self.patient=Paciente.objects.create(nombre='ANA',appat='LOPEZ',apmat='DIAZ',fecha_nacimiento='1990-01-01',genero='F',telefono='1111111111',email='A@EXAMPLE.COM',medico=self.owner)
        self.client.force_authenticate(self.owner)

    def test_empty_get_does_not_create_and_matches_ui_contract(self):
        response=self.client.get(reverse('api-odontogram',args=[self.patient.id]))
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.data['denticion_permanente'],{})
        self.assertFalse(Odontograma.objects.exists())

    def test_put_creates_then_updates_single_legacy_resource(self):
        payload={'denticion_permanente':{'11':{'oclusal':'caries'}},'denticion_decidua':{},'resumen':{'total_dientes':52}}
        first=self.client.put(reverse('api-odontogram',args=[self.patient.id]),payload,format='json')
        self.assertEqual(first.status_code,200)
        payload['denticion_permanente']['11']['oclusal']='restauracion'
        second=self.client.put(reverse('api-odontogram',args=[self.patient.id]),payload,format='json')
        self.assertEqual(second.data['denticion_permanente']['11']['oclusal'],'restauracion')
        self.assertEqual(Odontograma.objects.filter(paciente=self.patient).count(),1)

    def test_foreign_patient_is_hidden(self):
        foreign=Paciente.objects.create(nombre='B',appat='B',apmat='B',fecha_nacimiento='1990-01-01',genero='M',telefono='2222222222',email='B@EXAMPLE.COM',medico=self.other)
        self.assertEqual(self.client.get(reverse('api-odontogram',args=[foreign.id])).status_code,404)

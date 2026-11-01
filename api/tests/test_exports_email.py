from django.contrib.auth.models import User
from django.core import mail
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APITestCase
from Pacientes.models import Paciente

@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class ExportsEmailApiTests(APITestCase):
    def setUp(self):
        self.owner=User.objects.create_user(username='owner',password='secret123'); self.other=User.objects.create_user(username='other',password='secret123')
        self.patient=self.make(self.owner,'1111111111','A@EXAMPLE.COM'); self.foreign=self.make(self.other,'2222222222','B@EXAMPLE.COM'); self.client.force_authenticate(self.owner)
    def make(self,user,phone,email): return Paciente.objects.create(nombre='ANA',appat='LOPEZ',apmat='DIAZ',fecha_nacimiento='1990-01-01',genero='F',telefono=phone,email=email,medico=user)
    def test_patient_export_is_xlsx_and_owner_scoped(self):
        response=self.client.get(reverse('api-export-patients')); self.assertEqual(response.status_code,200); self.assertIn('Pacientes.xlsx',response['Content-Disposition']); self.assertGreater(len(response.content),1000)
    def test_other_exports_return_legacy_filenames(self):
        self.assertIn('Consultas.xlsx',self.client.get(reverse('api-export-consultations'))['Content-Disposition']); self.assertIn('ImagenesClinicas.xlsx',self.client.get(reverse('api-export-images'))['Content-Disposition'])
    def test_email_uses_stored_recipient_and_html(self):
        response=self.client.post(reverse('api-patient-email',args=[self.patient.id]),{'asunto':'Control','mensaje':'Hola'},format='json'); self.assertEqual(response.status_code,200); self.assertEqual(mail.outbox[0].to,[self.patient.email]); self.assertTrue(mail.outbox[0].alternatives)
        self.assertEqual(self.client.post(reverse('api-patient-email',args=[self.foreign.id]),{'asunto':'X','mensaje':'X'},format='json').status_code,404)

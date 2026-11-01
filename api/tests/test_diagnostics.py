from unittest.mock import patch
import shutil
import tempfile
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APITestCase
from Pacientes.models import Consulta, ImagenesClinicas, Paciente

def upload(name): return SimpleUploadedFile(name,b'GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00ccc,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;',content_type='image/gif')
TEST_MEDIA=tempfile.mkdtemp()

@override_settings(MEDIA_ROOT=TEST_MEDIA)
class DiagnosticsApiTests(APITestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass(); shutil.rmtree(TEST_MEDIA,ignore_errors=True)
    def setUp(self):
        self.owner=User.objects.create_user(username='owner'); self.other=User.objects.create_user(username='other')
        self.patient=self.make_patient(self.owner,'1','a@a.com'); self.foreign=self.make_patient(self.other,'2','b@b.com'); self.client.force_authenticate(self.owner)
        consultation=Consulta.objects.create(paciente=self.patient,medico=self.owner,fecha_consulta=timezone.now(),motivo_consulta='X')
        self.image=ImagenesClinicas.objects.create(paciente=self.patient,consulta=consultation,medico=self.owner,tipo_imagen='RX',descripcion='X',imagen=upload('x.gif'))
    def make_patient(self,user,phone,email): return Paciente.objects.create(nombre='ANA',appat='LOPEZ',apmat='DIAZ',fecha_nacimiento='1990-01-01',genero='F',telefono=phone,email=email,medico=user)
    def test_list_statistics_filters_and_owner_scope(self):
        response=self.client.get(reverse('api-diagnostics'),{'patient':'ana','type':'RX'}); self.assertEqual(response.status_code,200); self.assertEqual(response.data['count'],1); self.assertEqual(response.data['statistics']['pending'],1); self.assertEqual(response.data['results'][0]['patient_name'],'ANA LOPEZ')
    @patch('api.views.analyze_clinical_image')
    def test_analyze_returns_detections(self,analyze):
        analyze.return_value=[{'clase':'Cavity','confianza':.9,'coordenadas':[1,2,3,4]}]
        response=self.client.post(reverse('api-clinical-image-analyze',args=[self.image.id])); self.assertEqual(response.status_code,200); self.assertEqual(response.data['detections'][0]['clase'],'Cavity'); analyze.assert_called_once()

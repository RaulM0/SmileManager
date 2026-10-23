import shutil
import tempfile
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APITestCase
from Pacientes.models import Consentimiento, EstudioComparativo, Paciente

TEST_MEDIA=tempfile.mkdtemp()
def image(name): return SimpleUploadedFile(name,b'GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00ccc,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;',content_type='image/gif')

@override_settings(MEDIA_ROOT=TEST_MEDIA)
class StudyConsentApiTests(APITestCase):
    @classmethod
    def tearDownClass(cls): super().tearDownClass(); shutil.rmtree(TEST_MEDIA,ignore_errors=True)
    def setUp(self):
        self.owner=User.objects.create_user(username='owner',password='secret123'); self.other=User.objects.create_user(username='other',password='secret123')
        self.patient=Paciente.objects.create(nombre='ANA',appat='LOPEZ',apmat='DIAZ',fecha_nacimiento='1990-01-01',genero='F',telefono='1111111111',email='A@EXAMPLE.COM',medico=self.owner); self.client.force_authenticate(self.owner)
    def study_payload(self):
        return {'fecha_inicio':'2026-01-01','diagnostico':'Caso','observaciones':'Notas','antes_oclusal_superior':image('a.gif'),'antes_lateral_izquierda':image('b.gif'),'antes_frontal':image('c.gif'),'antes_lateral_derecha':image('d.gif'),'antes_oclusal_inferior':image('e.gif')}
    def test_study_requires_five_before_images_and_updates(self):
        url=reverse('api-comparative-study',args=[self.patient.id]); self.assertEqual(self.client.put(url,{'fecha_inicio':'2026-01-01'},format='multipart').status_code,400)
        created=self.client.put(url,self.study_payload(),format='multipart'); self.assertEqual(created.status_code,200,created.data); self.assertTrue(created.data['exists']); self.assertEqual(EstudioComparativo.objects.count(),1)
        updated=self.client.put(url,{'diagnostico':'Actualizado'},format='multipart'); self.assertEqual(updated.status_code,200); self.assertEqual(EstudioComparativo.objects.get().diagnostico,'Actualizado')
    def test_consent_requires_valid_file_and_becomes_read_only(self):
        url=reverse('api-consent',args=[self.patient.id]); self.assertEqual(self.client.get(url).status_code,200); self.assertEqual(self.client.post(url,{},format='multipart').status_code,400)
        accepted=self.client.post(url,{'texto':'Acepto','archivo_ine':image('ine.gif')},format='multipart'); self.assertEqual(accepted.status_code,200); self.assertIsNotNone(Consentimiento.objects.get().fecha_aceptacion); self.assertEqual(self.client.post(url,{'archivo_ine':image('x.gif')},format='multipart').status_code,409)
    def test_study_pdf_preserves_legacy_download(self):
        study_url=reverse('api-comparative-study',args=[self.patient.id]); self.client.put(study_url,self.study_payload(),format='multipart')
        response=self.client.get(reverse('api-comparative-study-pdf',args=[self.patient.id]))
        self.assertEqual(response.status_code,200); self.assertEqual(response['Content-Type'],'application/pdf'); self.assertTrue(response.content.startswith(b'%PDF'))
    def test_foreign_resources_are_hidden(self):
        foreign=Paciente.objects.create(nombre='B',appat='B',apmat='B',fecha_nacimiento='1990-01-01',genero='M',telefono='2222222222',email='B@EXAMPLE.COM',medico=self.other)
        self.assertEqual(self.client.get(reverse('api-comparative-study',args=[foreign.id])).status_code,404); self.assertEqual(self.client.get(reverse('api-consent',args=[foreign.id])).status_code,404)

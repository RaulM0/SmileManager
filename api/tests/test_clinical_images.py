import shutil
import tempfile
from datetime import datetime

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from Pacientes.models import Consulta, ImagenesClinicas, Paciente


TEST_MEDIA = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=TEST_MEDIA)
class ClinicalImageApiTests(APITestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEST_MEDIA, ignore_errors=True)

    def setUp(self):
        self.owner = User.objects.create_user(username='owner', password='secret123')
        self.other = User.objects.create_user(username='other', password='secret123')
        self.patient = self.patient_for(self.owner, '1111111111', 'A@EXAMPLE.COM')
        self.foreign = self.patient_for(self.other, '2222222222', 'B@EXAMPLE.COM')
        self.consultation = Consulta.objects.create(paciente=self.patient, medico=self.owner, fecha_consulta=timezone.now(), motivo_consulta='CONTROL')
        self.foreign_consultation = Consulta.objects.create(paciente=self.foreign, medico=self.other, fecha_consulta=timezone.now(), motivo_consulta='AJENA')
        self.client.force_authenticate(self.owner)

    def patient_for(self, owner, phone, email):
        return Paciente.objects.create(nombre='ANA',appat='LOPEZ',apmat='DIAZ',fecha_nacimiento='1990-01-01',genero='F',telefono=phone,email=email,medico=owner)

    def image_file(self, name='test.gif'):
        return SimpleUploadedFile(name, b'GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00ccc,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;', content_type='image/gif')

    def test_upload_normalizes_and_links_owned_consultation(self):
        response = self.client.post(reverse('api-clinical-images', args=[self.patient.id]), {'consulta_id':self.consultation.id,'tipo_imagen':'radiografía','descripcion':'control','imagen':self.image_file()}, format='multipart')
        self.assertEqual(response.status_code, 201, response.data)
        image = ImagenesClinicas.objects.get(pk=response.data['id'])
        self.assertEqual(image.tipo_imagen, 'RADIOGRAFÍA')
        self.assertEqual(image.descripcion, 'CONTROL')
        self.assertEqual(image.medico, self.owner)
        self.assertTrue(response.data['imagen_url'])

    def test_rejects_foreign_consultation_and_patient(self):
        response = self.client.post(reverse('api-clinical-images', args=[self.patient.id]), {'consulta_id':self.foreign_consultation.id,'tipo_imagen':'x','descripcion':'x','imagen':self.image_file()}, format='multipart')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.client.get(reverse('api-clinical-images', args=[self.foreign.id])).status_code, 404)

    def test_list_filters_and_delete_are_owner_scoped(self):
        image = ImagenesClinicas.objects.create(paciente=self.patient,consulta=self.consultation,medico=self.owner,tipo_imagen='RX',descripcion='CONTROL',imagen=self.image_file('owned.gif'))
        listing = self.client.get(reverse('api-clinical-images', args=[self.patient.id]), {'consultation_id':self.consultation.id,'date':timezone.localdate().isoformat()})
        self.assertEqual([item['id'] for item in listing.data], [image.id])
        response = self.client.delete(reverse('api-clinical-image-detail', args=[image.id]))
        self.assertEqual(response.status_code, 204)
        self.assertFalse(ImagenesClinicas.objects.filter(pk=image.id).exists())

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from Pacientes.models import Paciente, ImagenesClinicas
from Usuarios.models import AuditEvent


class LegacyPatientSecurityTests(TestCase):
    def test_create_uses_validation_and_audit(self):
        user = User.objects.create_user('legacy-create')
        self.client.force_login(user)
        response = self.client.post(reverse('registrar_pacientes'), {'nombre': 'Ana', 'appat': 'B', 'apmat': 'C', 'fecha_nacimiento': '1990-01-01', 'genero': 'F', 'telefono': '1234567890', 'email': 'synthetic@example.test'})
        self.assertEqual(response.status_code, 302)
        patient = Paciente.objects.get(medico=user)
        self.assertEqual(patient.nombre, 'ANA')
        self.assertTrue(AuditEvent.objects.filter(action='PATIENT_CREATE', actor=user, resource_id=str(patient.pk)).exists())

    def test_edit_and_deactivate_use_owner_and_record_success(self):
        owner = User.objects.create_user('legacy-owner')
        other = User.objects.create_user('legacy-other')
        patient = Paciente.objects.create(nombre='A', appat='B', apmat='C', fecha_nacimiento='1990-01-01', genero='F', telefono='1234567890', email='synthetic@example.test', medico=owner)
        self.client.force_login(other)
        self.client.post(reverse('editar_paciente', args=[patient.pk]), {'nombre': 'foreign'})
        patient.refresh_from_db()
        self.assertEqual(patient.nombre, 'A')
        self.assertFalse(AuditEvent.objects.filter(action='PATIENT_UPDATE').exists())
        self.client.force_login(owner)
        response = self.client.post(reverse('editar_paciente', args=[patient.pk]), {'nombre': 'nuevo'})
        self.assertEqual(response.status_code, 302)
        patient.refresh_from_db()
        self.assertEqual(patient.nombre, 'NUEVO')
        self.assertEqual(patient.estatus, 'A')
        self.assertTrue(AuditEvent.objects.filter(action='PATIENT_UPDATE', actor=owner, resource_id=str(patient.pk)).exists())
        self.client.post(reverse('eliminar_paciente', args=[patient.pk]))
        patient.refresh_from_db()
        self.assertEqual(patient.estatus, 'I')
        self.assertTrue(AuditEvent.objects.filter(action='PATIENT_DEACTIVATE', actor=owner).exists())

    def test_image_delete_requires_post_and_owner_and_audits(self):
        owner = User.objects.create_user('image-owner')
        other = User.objects.create_user('image-other')
        patient = Paciente.objects.create(nombre='A', appat='B', apmat='C', fecha_nacimiento='1990-01-01', genero='F', telefono='1234567890', email='synthetic@example.test', medico=owner)
        image = ImagenesClinicas.objects.create(paciente=patient, medico=owner, imagen='synthetic.png', tipo_imagen='RX')
        url = reverse('eliminar_imagen', args=[image.pk])
        self.client.force_login(owner)
        self.assertEqual(self.client.get(url).status_code, 405)
        self.client.force_login(other)
        self.assertEqual(self.client.post(url).status_code, 404)
        self.assertTrue(ImagenesClinicas.objects.filter(pk=image.pk).exists())
        self.client.force_login(owner)
        self.assertEqual(self.client.post(url).status_code, 302)
        self.assertTrue(AuditEvent.objects.filter(action='CLINICAL_IMAGE_DELETE', actor=owner, resource_id=str(image.pk)).exists())

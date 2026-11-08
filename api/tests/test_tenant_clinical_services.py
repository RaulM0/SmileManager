from django.contrib.auth.models import User
from django.http import Http404
from django.test import TestCase
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied

from Pacientes.models import Consulta, ImagenesClinicas, Paciente
from Usuarios.models import Clinic, ClinicMembership
from api.services.clinical_images import create_clinical_image
from api.services.consultations import create_consultation
from api.services.patients import create_patient, deactivate_patient, update_patient


class TenantClinicalServiceTests(TestCase):
    def setUp(self):
        self.doctor = User.objects.create_user('service-tenant-doctor')
        self.other = User.objects.create_user('service-other-doctor')
        self.a = Clinic.objects.create(name='A', slug='service-clinic-a', status='ACTIVE')
        self.b = Clinic.objects.create(name='B', slug='service-clinic-b', status='ACTIVE')
        self.membership = ClinicMembership.objects.create(user=self.doctor, clinic=self.a, role='DOCTOR', status='ACTIVE')
        self.patient = Paciente.objects.create(clinic=self.b, medico=self.doctor, nombre='Sintético', appat='Prueba', apmat='Demo', fecha_nacimiento='2000-01-01', genero='F', telefono='5553333333', email='service@example.test')
        self.consultation = Consulta.objects.create(paciente=self.patient, medico=self.doctor, motivo_consulta='Sintético', fecha_consulta=timezone.now())

    def test_service_cannot_create_consultation_for_foreign_clinic_or_without_context(self):
        for clinic_id in (self.a.pk, None):
            with self.assertRaises(Http404):
                create_consultation(patient=self.patient, medico=self.doctor, clinic_id=clinic_id, validated_data={'motivo_consulta': 'no autorizado'})
        self.assertEqual(Consulta.objects.count(), 1)

    def test_service_cannot_create_image_for_foreign_clinic_or_without_context(self):
        values = {'consulta_id': self.consultation.pk, 'tipo_imagen': 'RX', 'descripcion': 'sintética', 'imagen': 'synthetic.png'}
        for clinic_id in (self.a.pk, None):
            with self.assertRaises(Http404):
                create_clinical_image(patient=self.patient, medico=self.doctor, clinic_id=clinic_id, validated_data=values.copy())
        self.assertFalse(ImagenesClinicas.objects.exists())

    def test_revoked_membership_cannot_call_service_directly(self):
        self.patient.clinic = self.a
        self.patient.save(update_fields=['clinic'])
        self.membership.status = 'REVOKED'
        self.membership.save(update_fields=['status'])
        with self.assertRaises(PermissionDenied):
            create_consultation(patient=self.patient, medico=self.doctor, clinic_id=self.a.pk, validated_data={'motivo_consulta': 'no autorizado'})

    def test_patient_mutations_revalidate_context_and_refuse_ownership_changes(self):
        with self.assertRaises(Http404):
            update_patient(patient=self.patient, medico=self.doctor, clinic_id=self.a.pk, validated_data={'nombre': 'incorrecto'})
        with self.assertRaises(Http404):
            deactivate_patient(patient=self.patient, user=self.doctor, clinic_id=self.a.pk)
        self.patient.clinic = self.a
        self.patient.save(update_fields=['clinic'])
        with self.assertRaises(PermissionDenied):
            update_patient(patient=self.patient, medico=self.doctor, clinic_id=self.a.pk, validated_data={'clinic_id': self.b.pk})
        self.patient.refresh_from_db()
        self.assertEqual((self.patient.clinic_id, self.patient.estatus, self.patient.nombre), (self.a.pk, 'A', 'Sintético'))

    def test_creation_rejects_clinic_object_in_untrusted_values(self):
        with self.assertRaises(PermissionDenied):
            create_patient(medico=self.other, validated_data={'clinic': self.a, 'nombre': 'No autorizado'})
        self.assertEqual(Paciente.objects.count(), 1)

from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from Pacientes.models import Consulta, Paciente
from Usuarios.models import AuditEvent, Clinic, ClinicMembership


class TenantConsultationTests(APITestCase):
    def setUp(self):
        self.doctor = User.objects.create_user('tenant-consultation-doctor')
        self.a = Clinic.objects.create(name='A', slug='consultation-a', status='ACTIVE')
        self.b = Clinic.objects.create(name='B', slug='consultation-b', status='ACTIVE')
        self.member = ClinicMembership.objects.create(user=self.doctor, clinic=self.a, role='DOCTOR', status='ACTIVE')
        ClinicMembership.objects.create(user=self.doctor, clinic=self.b, role='DOCTOR', status='ACTIVE')
        self.patient_a = self.patient(self.a, '1111111111')
        self.patient_b = self.patient(self.b, '2222222222')
        self.foreign = Consulta.objects.create(paciente=self.patient_b, medico=self.doctor, fecha_consulta=timezone.now(), motivo_consulta='B')
        self.client.force_authenticate(self.doctor)

    def patient(self, clinic, phone):
        return Paciente.objects.create(nombre='A', appat='B', apmat='C', fecha_nacimiento='2000-01-01', genero='F', telefono=phone, email=f'{phone}@example.test', medico=self.doctor, clinic=clinic)

    def test_cross_clinic_reads_and_writes_denied(self):
        foreign_list = reverse('tenant-consultations', args=[self.patient_b.pk])
        foreign_detail = reverse('tenant-consultation-detail', args=[self.foreign.pk])
        self.assertEqual(self.client.get(foreign_list, HTTP_X_CLINIC_ID=str(self.a.pk)).status_code, 404)
        self.assertEqual(self.client.post(foreign_list, {'motivo_consulta': 'test'}, format='json', HTTP_X_CLINIC_ID=str(self.a.pk)).status_code, 404)
        self.assertEqual(self.client.get(foreign_detail, HTTP_X_CLINIC_ID=str(self.a.pk)).status_code, 404)

    def test_create_is_server_assigned_and_audited(self):
        url = reverse('tenant-consultations', args=[self.patient_a.pk])
        forged = {'motivo_consulta': 'control', 'paciente_id': self.patient_b.pk}
        self.assertEqual(self.client.post(url, forged, format='json', HTTP_X_CLINIC_ID=str(self.a.pk)).status_code, 400)
        response = self.client.post(url, {'motivo_consulta': 'control'}, format='json', HTTP_X_CLINIC_ID=str(self.a.pk))
        self.assertEqual(response.status_code, 201, response.data)
        consultation = Consulta.objects.get(pk=response.data['id'])
        self.assertEqual((consultation.paciente_id, consultation.medico_id), (self.patient_a.pk, self.doctor.pk))
        self.assertTrue(AuditEvent.objects.filter(action='TENANT_CONSULTATION_CREATED', clinic=self.a, resource_id=str(consultation.pk)).exists())
        self.member.status = 'REVOKED'
        self.member.save(update_fields=['status'])
        self.assertEqual(self.client.get(url, HTTP_X_CLINIC_ID=str(self.a.pk)).status_code, 403)

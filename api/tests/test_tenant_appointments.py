from datetime import timedelta

from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from Citas.models import Cita
from Pacientes.models import Paciente
from Usuarios.models import AuditEvent, Clinic, ClinicMembership


class TenantAppointmentTests(APITestCase):
    def setUp(self):
        self.doctor = User.objects.create_user('appointment-doctor')
        self.a = Clinic.objects.create(name='A', slug='appointment-a', status='ACTIVE')
        self.b = Clinic.objects.create(name='B', slug='appointment-b', status='ACTIVE')
        self.member_a = ClinicMembership.objects.create(user=self.doctor, clinic=self.a, role='DOCTOR', status='ACTIVE')
        ClinicMembership.objects.create(user=self.doctor, clinic=self.b, role='DOCTOR', status='ACTIVE')
        self.patient_a = self.patient(self.a, '1111111111')
        self.patient_b = self.patient(self.b, '2222222222')
        self.appointment_a = Cita.objects.create(paciente=self.patient_a, fecha=timezone.localdate()+timedelta(days=1), hora='10:00', motivo='A')
        self.appointment_b = Cita.objects.create(paciente=self.patient_b, fecha=timezone.localdate()+timedelta(days=1), hora='10:00', motivo='B')
        self.client.force_authenticate(self.doctor)

    def patient(self, clinic, phone):
        return Paciente.objects.create(nombre='A', appat='B', apmat='C', fecha_nacimiento='2000-01-01', genero='F', telefono=phone, email=f'{phone}@example.test', medico=self.doctor, clinic=clinic)

    def payload(self, patient):
        return {'paciente_id': patient.pk, 'fecha': str(timezone.localdate()+timedelta(days=1)), 'hora': '11:00', 'motivo': 'CONTROL'}

    def test_list_and_detail_never_include_other_clinic(self):
        response = self.client.get(reverse('tenant-appointment-list'), HTTP_X_CLINIC_ID=str(self.a.pk))
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item['id'] for item in response.data['results']], [self.appointment_a.pk])
        url = reverse('tenant-appointment-detail', args=[self.appointment_b.pk])
        self.assertEqual(self.client.get(url, HTTP_X_CLINIC_ID=str(self.a.pk)).status_code, 404)
        self.assertEqual(self.client.patch(url, {'motivo': 'CAMBIO'}, format='json', HTTP_X_CLINIC_ID=str(self.a.pk)).status_code, 404)
        self.appointment_b.refresh_from_db()
        self.assertEqual(self.appointment_b.motivo, 'B')

    def test_create_rejects_cross_clinic_patient_and_forged_context(self):
        url = reverse('tenant-appointment-list')
        self.assertEqual(self.client.post(url, self.payload(self.patient_b), format='json', HTTP_X_CLINIC_ID=str(self.a.pk)).status_code, 400)
        forged = {**self.payload(self.patient_a), 'clinic_id': str(self.b.pk)}
        self.assertEqual(self.client.post(url, forged, format='json', HTTP_X_CLINIC_ID=str(self.a.pk)).status_code, 400)
        response = self.client.post(url, self.payload(self.patient_a), format='json', HTTP_X_CLINIC_ID=str(self.a.pk))
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(Cita.objects.get(pk=response.data['id']).paciente_id, self.patient_a.pk)
        self.assertTrue(AuditEvent.objects.filter(action='TENANT_APPOINTMENT_CREATED', clinic=self.a, resource_id=str(response.data['id'])).exists())

    def test_update_checks_patient_link_and_transition(self):
        url = reverse('tenant-appointment-detail', args=[self.appointment_a.pk])
        response = self.client.patch(url, {'paciente_id': self.patient_b.pk}, format='json', HTTP_X_CLINIC_ID=str(self.a.pk))
        self.assertEqual(response.status_code, 400)
        response = self.client.patch(url, {'estatus': 'C'}, format='json', HTTP_X_CLINIC_ID=str(self.a.pk))
        self.assertEqual(response.status_code, 200)
        response = self.client.patch(url, {'estatus': 'P'}, format='json', HTTP_X_CLINIC_ID=str(self.a.pk))
        self.assertEqual(response.status_code, 409)
        self.assertTrue(AuditEvent.objects.filter(action='TENANT_APPOINTMENT_UPDATED', clinic=self.a, resource_id=str(self.appointment_a.pk)).exists())

    def test_membership_revocation_prevents_access(self):
        self.member_a.status = 'REVOKED'
        self.member_a.save(update_fields=['status'])
        response = self.client.get(reverse('tenant-appointment-list'), HTTP_X_CLINIC_ID=str(self.a.pk))
        self.assertEqual(response.status_code, 403)

    def test_transition_and_filters_are_clinic_scoped(self):
        date = str(timezone.localdate()+timedelta(days=1))
        listing = self.client.get(reverse('tenant-appointment-list'), {'from': date, 'to': date}, HTTP_X_CLINIC_ID=str(self.a.pk))
        self.assertEqual([item['id'] for item in listing.data['results']], [self.appointment_a.pk])
        foreign = reverse('tenant-appointment-transition', args=[self.appointment_b.pk, 'cancel'])
        self.assertEqual(self.client.post(foreign, HTTP_X_CLINIC_ID=str(self.a.pk)).status_code, 404)
        own = reverse('tenant-appointment-transition', args=[self.appointment_a.pk, 'complete'])
        self.assertEqual(self.client.post(own, HTTP_X_CLINIC_ID=str(self.a.pk)).status_code, 200)
        self.appointment_a.refresh_from_db()
        self.assertEqual(self.appointment_a.estatus, 'C')

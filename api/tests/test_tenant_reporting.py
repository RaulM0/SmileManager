from datetime import timedelta
from io import BytesIO

from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from openpyxl import load_workbook
from rest_framework.test import APITestCase

from Citas.models import Cita
from Pacientes.models import Paciente
from Usuarios.models import AuditEvent, Clinic, ClinicMembership


class TenantReportingTests(APITestCase):
    def setUp(self):
        self.doctor = User.objects.create_user('report-doctor')
        self.admin = User.objects.create_user('report-admin')
        self.staff = User.objects.create_user('report-staff')
        self.a = Clinic.objects.create(name='A', slug='report-a', status='ACTIVE')
        self.b = Clinic.objects.create(name='B', slug='report-b', status='ACTIVE')
        ClinicMembership.objects.create(user=self.doctor, clinic=self.a, role='DOCTOR', status='ACTIVE')
        ClinicMembership.objects.create(user=self.doctor, clinic=self.b, role='DOCTOR', status='ACTIVE')
        ClinicMembership.objects.create(user=self.admin, clinic=self.a, role='CLINIC_ADMIN', status='ACTIVE')
        ClinicMembership.objects.create(user=self.staff, clinic=self.a, role='STAFF', status='ACTIVE')
        self.patient_a = self.patient(self.a, 'PACIENTE_A', '1111111111')
        self.patient_b = self.patient(self.b, 'PACIENTE_B', '2222222222')
        for patient in (self.patient_a, self.patient_b):
            Cita.objects.create(paciente=patient, fecha=timezone.localdate()+timedelta(days=1), hora='10:00', motivo='control')

    def patient(self, clinic, name, phone):
        return Paciente.objects.create(nombre=name, appat='B', apmat='C', fecha_nacimiento='2000-01-01', genero='F', telefono=phone, email=f'{phone}@example.test', medico=self.doctor, clinic=clinic)

    def test_doctor_dashboard_and_export_exclude_other_clinic(self):
        self.client.force_authenticate(self.doctor)
        dashboard = self.client.get(reverse('tenant-doctor-dashboard'), HTTP_X_CLINIC_ID=str(self.a.pk))
        self.assertEqual(dashboard.status_code, 200)
        self.assertEqual(dashboard.data['patient_count'], 1)
        self.assertEqual(len(dashboard.data['upcoming']), 1)
        response = self.client.get(reverse('tenant-clinical-export', args=['patients']), HTTP_X_CLINIC_ID=str(self.a.pk))
        self.assertEqual(response.status_code, 200)
        rows = list(load_workbook(BytesIO(response.content), read_only=True).active.values)
        self.assertIn('PACIENTE_A', str(rows))
        self.assertNotIn('PACIENTE_B', str(rows))
        self.assertIn('no-store', response['Cache-Control'])
        self.assertTrue(AuditEvent.objects.filter(clinic=self.a, actor=self.doctor, action='TENANT_CLINICAL_EXPORT').exists())

    def test_clinic_admin_sees_only_aggregate_metrics_for_own_clinic(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get(reverse('tenant-admin-dashboard'), HTTP_X_CLINIC_ID=str(self.a.pk))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['patients']['active'], 1)
        self.assertEqual(response.data['appointments']['pending'], 1)
        self.assertEqual(response.data['members'], {'doctors': 1, 'staff': 1})
        self.assertNotIn('PACIENTE_A', str(response.data))
        self.assertEqual(self.client.get(reverse('tenant-admin-dashboard'), HTTP_X_CLINIC_ID=str(self.b.pk)).status_code, 403)
        self.assertEqual(self.client.get(reverse('tenant-patient-detail', args=[self.patient_a.pk]), HTTP_X_CLINIC_ID=str(self.a.pk)).status_code, 403)

    def test_staff_cannot_export_or_open_admin_dashboard(self):
        self.client.force_authenticate(self.staff)
        self.assertEqual(self.client.get(reverse('tenant-clinical-export', args=['patients']), HTTP_X_CLINIC_ID=str(self.a.pk)).status_code, 403)
        self.assertEqual(self.client.get(reverse('tenant-admin-dashboard'), HTTP_X_CLINIC_ID=str(self.a.pk)).status_code, 403)

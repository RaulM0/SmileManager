from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase

from Pacientes.models import AntescedentesMedicos, ClinicalRevision, Paciente
from Usuarios.models import AuditEvent, Clinic, ClinicMembership


class TenantClinicalRecordTests(APITestCase):
    def setUp(self):
        self.doctor = User.objects.create_user('clinical-tenant-doctor')
        self.a = Clinic.objects.create(name='A', slug='clinical-tenant-a', status='ACTIVE')
        self.b = Clinic.objects.create(name='B', slug='clinical-tenant-b', status='ACTIVE')
        self.membership = ClinicMembership.objects.create(user=self.doctor, clinic=self.a, role='DOCTOR', status='ACTIVE')
        ClinicMembership.objects.create(user=self.doctor, clinic=self.b, role='DOCTOR', status='ACTIVE')
        self.patient_a = self.patient(self.a, '1111111111')
        self.patient_b = self.patient(self.b, '2222222222')
        self.client.force_authenticate(self.doctor)

    def patient(self, clinic, phone):
        return Paciente.objects.create(nombre='A', appat='B', apmat='C', fecha_nacimiento='2000-01-01', genero='F', telefono=phone, email=f'{phone}@example.test', medico=self.doctor, clinic=clinic)

    def test_history_keeps_clinic_revision_and_conflict(self):
        url = reverse('tenant-medical-history', args=[self.patient_a.pk])
        response = self.client.put(url, {'version': 0, 'otros': 'primero'}, format='json', HTTP_X_CLINIC_ID=str(self.a.pk))
        self.assertEqual(response.status_code, 200, response.data)
        history = AntescedentesMedicos.objects.get(paciente=self.patient_a)
        revision = ClinicalRevision.objects.get(resource_type='medical_history', resource_id=history.pk, version=1)
        self.assertEqual((revision.clinic_id, revision.patient_id, revision.actor_id), (self.a.pk, self.patient_a.pk, self.doctor.pk))
        self.assertEqual(self.client.put(url, {'version': 0, 'otros': 'perdido'}, format='json', HTTP_X_CLINIC_ID=str(self.a.pk)).status_code, 409)
        self.assertTrue(AuditEvent.objects.filter(action='TENANT_CLINICAL_HISTORY_UPDATED', clinic=self.a, actor=self.doctor).exists())

    def test_cross_clinic_and_forged_patient_denied(self):
        foreign = reverse('tenant-medical-history', args=[self.patient_b.pk])
        self.assertEqual(self.client.get(foreign, HTTP_X_CLINIC_ID=str(self.a.pk)).status_code, 404)
        self.assertEqual(self.client.put(foreign, {'version': 0}, format='json', HTTP_X_CLINIC_ID=str(self.a.pk)).status_code, 404)
        own = reverse('tenant-medical-history', args=[self.patient_a.pk])
        self.assertEqual(self.client.put(own, {'version': 0, 'paciente_id': self.patient_b.pk}, format='json', HTTP_X_CLINIC_ID=str(self.a.pk)).status_code, 400)
        self.assertFalse(AntescedentesMedicos.objects.exists())

    def test_odontogram_version_and_membership_revocation(self):
        url = reverse('tenant-odontogram', args=[self.patient_a.pk])
        payload = {'version': 0, 'denticion_permanente': {'11': {'oclusal': 'caries'}}, 'denticion_decidua': {}, 'resumen': {}}
        self.assertEqual(self.client.put(url, payload, format='json', HTTP_X_CLINIC_ID=str(self.a.pk)).status_code, 200)
        self.assertEqual(self.client.put(url, payload, format='json', HTTP_X_CLINIC_ID=str(self.a.pk)).status_code, 409)
        self.assertEqual(ClinicalRevision.objects.get(resource_type='odontogram').clinic_id, self.a.pk)
        self.membership.status = 'REVOKED'
        self.membership.save(update_fields=['status'])
        self.assertEqual(self.client.get(url, HTTP_X_CLINIC_ID=str(self.a.pk)).status_code, 403)

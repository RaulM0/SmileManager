from django.contrib.auth.models import User
from django.db import IntegrityError, close_old_connections, transaction
from django.test import TransactionTestCase, skipUnlessDBFeature
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework.test import APIClient
from api.authentication import SessionRefreshToken as RefreshToken
from concurrent.futures import ThreadPoolExecutor
import threading
from unittest.mock import patch

from Pacientes.models import Paciente
from Usuarios.models import AuditEvent, Clinic, ClinicMembership
from api.tenant_patients import TenantPatientMixin


class TenantPatientApiTests(APITestCase):
    def setUp(self):
        self.doctor = User.objects.create_user('tenant-doctor')
        self.other = User.objects.create_user('tenant-other')
        self.a = Clinic.objects.create(name='A', slug='tenant-patient-a', status='ACTIVE')
        self.b = Clinic.objects.create(name='B', slug='tenant-patient-b', status='ACTIVE')
        self.member_a = ClinicMembership.objects.create(clinic=self.a, user=self.doctor, role='DOCTOR', status='ACTIVE')
        self.member_b = ClinicMembership.objects.create(clinic=self.b, user=self.doctor, role='DOCTOR', status='ACTIVE')
        self.patient_a = self.patient('A', self.a, self.doctor, '1111111111')
        self.patient_b = self.patient('B', self.b, self.doctor, '2222222222')
        self.patient_other = self.patient('C', self.a, self.other, '3333333333')
        self.patient_unassigned = self.patient('D', None, self.doctor, '4444444444')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {RefreshToken.for_user(self.doctor).access_token}')

    @staticmethod
    def patient(name, clinic, doctor, phone):
        return Paciente.objects.create(nombre=name, appat='PRUEBA', apmat='DEMO', fecha_nacimiento='2000-01-01', genero='F', telefono=phone, email=f'{phone}@example.test', medico=doctor, clinic=clinic)

    @staticmethod
    def payload():
        return {'nombre': 'Nuevo', 'appat': 'Paciente', 'apmat': 'Prueba', 'fecha_nacimiento': '2000-01-01', 'genero': 'F', 'telefono': '5555555555', 'email': 'new@example.test'}

    def test_list_and_detail_require_clinic_and_assignment(self):
        url = reverse('tenant-patient-list')
        self.assertEqual(self.client.get(url).status_code, 403)
        response = self.client.get(url, HTTP_X_CLINIC_ID=str(self.a.pk))
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item['id'] for item in response.data['results']], [self.patient_a.pk])
        self.assertEqual(self.client.get(reverse('tenant-patient-detail', args=[self.patient_b.pk]), HTTP_X_CLINIC_ID=str(self.a.pk)).status_code, 404)
        self.assertEqual(self.client.get(reverse('tenant-patient-detail', args=[self.patient_other.pk]), HTTP_X_CLINIC_ID=str(self.a.pk)).status_code, 404)
        self.assertEqual(self.client.get(reverse('tenant-patient-detail', args=[self.patient_unassigned.pk]), HTTP_X_CLINIC_ID=str(self.a.pk)).status_code, 404)

    def test_create_uses_server_context_and_rejects_forged_clinic(self):
        url = reverse('tenant-patient-list')
        forged = {**self.payload(), 'clinic_id': str(self.b.pk)}
        self.assertEqual(self.client.post(url, forged, format='json', HTTP_X_CLINIC_ID=str(self.a.pk)).status_code, 400)
        response = self.client.post(url, self.payload(), format='json', HTTP_X_CLINIC_ID=str(self.a.pk))
        self.assertEqual(response.status_code, 201, response.data)
        patient = Paciente.objects.get(pk=response.data['id'])
        self.assertEqual((patient.clinic_id, patient.medico_id), (self.a.pk, self.doctor.pk))
        self.assertTrue(AuditEvent.objects.filter(action='TENANT_PATIENT_CREATED', clinic=self.a, actor=self.doctor, resource_id=str(patient.pk)).exists())

    def test_identical_contact_is_independent_between_clinics(self):
        url = reverse('tenant-patient-list')
        payload = self.payload()
        a = self.client.post(url, payload, format='json', HTTP_X_CLINIC_ID=str(self.a.pk))
        b = self.client.post(url, payload, format='json', HTTP_X_CLINIC_ID=str(self.b.pk))
        self.assertEqual(a.status_code, 201, a.data)
        self.assertEqual(b.status_code, 201, b.data)
        self.assertNotEqual(a.data['id'], b.data['id'])
        duplicate = self.client.post(url, payload, format='json', HTTP_X_CLINIC_ID=str(self.a.pk))
        self.assertEqual(duplicate.status_code, 400)
        self.assertEqual(self.client.get(reverse('tenant-patient-detail', args=[a.data['id']]), HTTP_X_CLINIC_ID=str(self.b.pk)).status_code, 404)

    def test_database_rejects_duplicate_contact_in_same_clinic(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Paciente.objects.create(nombre='X', appat='P', apmat='D', fecha_nacimiento='2000-01-01', genero='F', telefono=self.patient_a.telefono, email='unico@example.test', medico=self.doctor, clinic=self.a)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Paciente.objects.create(nombre='X', appat='P', apmat='D', fecha_nacimiento='2000-01-01', genero='F', telefono='9999999999', email=self.patient_a.email, medico=self.doctor, clinic=self.a)

    def test_cross_clinic_update_and_revocation_are_denied(self):
        url = reverse('tenant-patient-detail', args=[self.patient_b.pk])
        self.assertEqual(self.client.patch(url, {'nombre': 'CAMBIO'}, format='json', HTTP_X_CLINIC_ID=str(self.a.pk)).status_code, 404)
        self.member_b.status = 'REVOKED'
        self.member_b.save(update_fields=['status'])
        self.assertEqual(self.client.get(url, HTTP_X_CLINIC_ID=str(self.b.pk)).status_code, 403)
        self.patient_b.refresh_from_db()
        self.assertEqual(self.patient_b.nombre, 'B')

    def test_authorized_update_and_read_are_audited_in_clinic(self):
        url = reverse('tenant-patient-detail', args=[self.patient_a.pk])
        self.assertEqual(self.client.get(url, HTTP_X_CLINIC_ID=str(self.a.pk)).status_code, 200)
        self.assertEqual(self.client.patch(url, {'nombre': 'Actualizado'}, format='json', HTTP_X_CLINIC_ID=str(self.a.pk)).status_code, 200)
        self.patient_a.refresh_from_db()
        self.assertEqual(self.patient_a.nombre, 'ACTUALIZADO')
        self.assertEqual(AuditEvent.objects.filter(actor=self.doctor, clinic=self.a, resource_id=str(self.patient_a.pk), action__in=['TENANT_PATIENT_VIEWED', 'TENANT_PATIENT_UPDATED']).count(), 2)

    def test_suspended_clinic_and_non_doctor_denied(self):
        self.a.status = 'SUSPENDED'
        self.a.save(update_fields=['status'])
        self.assertEqual(self.client.get(reverse('tenant-patient-list'), HTTP_X_CLINIC_ID=str(self.a.pk)).status_code, 403)
        self.member_b.role = 'STAFF'
        self.member_b.save(update_fields=['role'])
        self.assertEqual(self.client.post(reverse('tenant-patient-list'), self.payload(), format='json', HTTP_X_CLINIC_ID=str(self.b.pk)).status_code, 403)

    def test_legacy_patient_routes_cannot_bypass_clinic_context(self):
        listing = self.client.get(reverse('api-patient-list'))
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(listing.data['count'], 0)
        self.assertEqual(self.client.get(reverse('api-patient-detail', args=[self.patient_a.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse('api-patient-detail', args=[self.patient_unassigned.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse('api-patient-list'), self.payload(), format='json').status_code, 403)

    def test_unaffiliated_user_cannot_access_assigned_patient_via_legacy_route(self):
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get(reverse('api-patient-detail', args=[self.patient_other.pk])).status_code, 404)

    def test_search_and_deactivate_remain_in_clinic(self):
        url = reverse('tenant-patient-autocomplete')
        response = self.client.get(url, {'term': self.patient_b.telefono}, HTTP_X_CLINIC_ID=str(self.a.pk))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'], [])
        response = self.client.get(url, {'term': self.patient_a.telefono}, HTTP_X_CLINIC_ID=str(self.a.pk))
        self.assertEqual([item['id'] for item in response.data['results']], [self.patient_a.pk])
        foreign = reverse('tenant-patient-deactivate', args=[self.patient_b.pk])
        self.assertEqual(self.client.post(foreign, HTTP_X_CLINIC_ID=str(self.a.pk)).status_code, 404)
        own = reverse('tenant-patient-deactivate', args=[self.patient_a.pk])
        self.assertEqual(self.client.post(own, HTTP_X_CLINIC_ID=str(self.a.pk)).status_code, 200)
        self.patient_a.refresh_from_db()
        self.assertEqual(self.patient_a.estatus, 'I')
        self.assertTrue(AuditEvent.objects.filter(action='TENANT_PATIENT_DEACTIVATED', clinic=self.a).exists())


@skipUnlessDBFeature('has_select_for_update')
class TenantPatientConcurrencyTests(TransactionTestCase):
    def test_revocation_committed_before_write_is_rechecked(self):
        doctor = User.objects.create_user('concurrent-tenant-doctor')
        clinic = Clinic.objects.create(name='A', slug='concurrent-patient-clinic', status='ACTIVE')
        membership = ClinicMembership.objects.create(user=doctor, clinic=clinic, role='DOCTOR', status='ACTIVE')
        locked, entered, release = threading.Event(), threading.Event(), threading.Event()
        original = TenantPatientMixin.lock_context

        def wrapped(view):
            entered.set()
            return original(view)

        def revoke():
            close_old_connections()
            try:
                with transaction.atomic():
                    Clinic.objects.select_for_update().get(pk=clinic.pk)
                    locked.set()
                    if not release.wait(10):
                        raise RuntimeError('Test synchronization timed out')
                    ClinicMembership.objects.filter(pk=membership.pk).update(status='REVOKED')
            finally:
                close_old_connections()

        def create():
            close_old_connections()
            try:
                client = APIClient()
                client.force_authenticate(doctor)
                return client.post(reverse('tenant-patient-list'), TenantPatientApiTests.payload(), format='json', HTTP_X_CLINIC_ID=str(clinic.pk)).status_code
            finally:
                close_old_connections()

        with patch.object(TenantPatientMixin, 'lock_context', wrapped), ThreadPoolExecutor(max_workers=2) as executor:
            revocation = executor.submit(revoke)
            try:
                self.assertTrue(locked.wait(10))
                creation = executor.submit(create)
                self.assertTrue(entered.wait(10))
            finally:
                release.set()
            revocation.result(timeout=15)
            self.assertEqual(creation.result(timeout=15), 403)
        self.assertFalse(Paciente.objects.filter(clinic=clinic).exists())

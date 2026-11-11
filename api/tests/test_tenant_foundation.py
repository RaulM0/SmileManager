from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import DataError, IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from api.authentication import SessionRefreshToken as RefreshToken
from io import StringIO

from api.services.clinics import transition_clinic
from Pacientes.access import clinic_clinical_queryset
from Usuarios.clinic_context import require_clinic_capability
from api.serializers import PatientSerializer
from Pacientes.models import ClinicalRevision, Paciente
from rest_framework.exceptions import PermissionDenied
from Usuarios.models import Clinic, ClinicMembership


class TenantFoundationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='doctor', password='secret')
        self.a = Clinic.objects.create(name='A', slug='a', status=Clinic.Status.ACTIVE)
        self.b = Clinic.objects.create(name='B', slug='b', status=Clinic.Status.ACTIVE)
        self.membership = ClinicMembership.objects.create(user=self.user, clinic=self.a, role=ClinicMembership.Role.DOCTOR, status=ClinicMembership.Status.ACTIVE)
        self.token = str(RefreshToken.for_user(self.user).access_token)

    def get_context(self, clinic):
        return self.client.get(reverse('clinic-context'), HTTP_AUTHORIZATION=f'Bearer {self.token}', HTTP_X_CLINIC_ID=str(clinic))

    def test_context_checks_membership_on_every_request(self):
        self.assertEqual(self.get_context(self.a.pk).status_code, 200)
        self.assertEqual(self.get_context(self.b.pk).status_code, 403)
        self.assertEqual(self.get_context('invalid').status_code, 403)
        self.membership.status = ClinicMembership.Status.REVOKED
        self.membership.save(update_fields=['status'])
        self.assertEqual(self.get_context(self.a.pk).status_code, 403)

    def test_suspension_and_multiple_memberships(self):
        ClinicMembership.objects.create(user=self.user, clinic=self.b, role=ClinicMembership.Role.STAFF, status=ClinicMembership.Status.ACTIVE)
        response = self.client.get(reverse('clinic-memberships'), HTTP_AUTHORIZATION=f'Bearer {self.token}')
        self.assertEqual(len(response.json()), 2)
        transition_clinic(clinic_id=self.a.pk, target=Clinic.Status.SUSPENDED)
        self.assertEqual(self.get_context(self.a.pk).status_code, 403)
        self.assertEqual(self.get_context(self.b.pk).status_code, 200)

    def test_membership_unique_even_if_revoked_and_role_validated_by_db(self):
        self.membership.status = ClinicMembership.Status.REVOKED
        self.membership.save(update_fields=['status'])
        with self.assertRaises(IntegrityError), transaction.atomic():
            ClinicMembership.objects.create(user=self.user, clinic=self.a, role=ClinicMembership.Role.DOCTOR)
        with self.assertRaises((IntegrityError, DataError)), transaction.atomic():
            ClinicMembership.objects.create(user=self.user, clinic=self.b, role='PLATFORM_ADMIN')
        with self.assertRaises(IntegrityError), transaction.atomic():
            ClinicMembership.objects.create(user=self.user, clinic=self.b, role='INVALID')

    def test_invalid_clinic_transition(self):
        with self.assertRaises(ValidationError):
            transition_clinic(clinic_id=self.a.pk, target='INVALID')

    def test_unauthenticated_context_denied(self):
        self.assertIn(self.client.get(reverse('clinic-memberships')).status_code, (401, 403))

    def test_inactive_user_with_existing_token_cannot_resolve(self):
        self.user.is_active = False
        self.user.save(update_fields=['is_active'])
        self.assertIn(self.get_context(self.a.pk).status_code, (401, 403))

    def test_inventory_reports_aggregate_without_writing(self):
        output = StringIO()
        call_command('inventory_tenant_migration', stdout=output)
        self.assertIn('patients_total=0', output.getvalue())
        self.assertIn('No clinic assignments were inferred or written.', output.getvalue())
        self.assertEqual(Clinic.objects.count(), 2)

    def test_capability_rechecks_role_and_membership(self):
        require_clinic_capability(self.user, self.a.pk, 'clinical.assigned')
        with self.assertRaises(PermissionDenied):
            require_clinic_capability(self.user, self.a.pk, 'membership.manage')
        self.membership.role = ClinicMembership.Role.STAFF
        self.membership.save(update_fields=['role'])
        with self.assertRaises(PermissionDenied):
            require_clinic_capability(self.user, self.a.pk, 'clinical.assigned')

    def test_inventory_detects_unassigned_and_mismatched_provenance(self):
        patient = Paciente.objects.create(nombre='A', appat='B', apmat='C', fecha_nacimiento='2000-01-01', genero='F', telefono='1234567890', email='test@example.com', medico=self.user, clinic=self.a)
        ClinicalRevision.objects.create(patient=patient, clinic=self.b, resource_type='history', resource_id=1, version=1, snapshot={})
        output = StringIO()
        call_command('inventory_tenant_migration', stdout=output)
        self.assertIn('revision_clinic_mismatch=1', output.getvalue())
        self.assertNotIn('clinic', PatientSerializer().fields)

    def test_clinical_queryset_requires_context_and_patient_assignment(self):
        other = User.objects.create_user(username='other')
        ClinicMembership.objects.create(user=self.user, clinic=self.b, role=ClinicMembership.Role.DOCTOR, status=ClinicMembership.Status.ACTIVE)
        def patient(name, clinic, doctor, number):
            return Paciente.objects.create(nombre=name, appat='B', apmat='C', fecha_nacimiento='2000-01-01', genero='F', telefono=number, email=f'{number}@example.com', medico=doctor, clinic=clinic)
        a = patient('A', self.a, self.user, '1000000000')
        patient('B', self.b, self.user, '2000000000')
        patient('C', self.a, other, '3000000000')
        patient('D', None, self.user, '4000000000')
        self.assertEqual(list(clinic_clinical_queryset(self.user, self.a.pk, Paciente)), [a])
        pending = clinic_clinical_queryset(self.user, self.a.pk, Paciente)
        self.membership.status = ClinicMembership.Status.REVOKED
        self.membership.save(update_fields=['status'])
        self.assertEqual(list(pending), [])
        with self.assertRaises(PermissionDenied):
            clinic_clinical_queryset(self.user, self.a.pk, Paciente)

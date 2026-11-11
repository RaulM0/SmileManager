from datetime import timedelta
from io import StringIO
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from Citas.models import Cita
from Pacientes.models import Paciente, Consentimiento
from Usuarios.models import AuditEvent, Clinic, ClinicMembership


@override_settings(LEGACY_CLINICAL_API_ENABLED=False)
class MultitenantClosureTests(APITestCase):
    def setUp(self):
        self.enterContext(override_settings(MEDIA_ROOT=self.enterContext(TemporaryDirectory())))
        self.a = Clinic.objects.create(name='Clínica A', slug='closure-a', status='ACTIVE')
        self.b = Clinic.objects.create(name='Clínica B', slug='closure-b', status='ACTIVE')
        self.doctor = User.objects.create_user('closure-doctor')
        self.staff = User.objects.create_user('closure-staff')
        self.admin = User.objects.create_user('closure-admin')
        for clinic in (self.a, self.b):
            ClinicMembership.objects.create(user=self.doctor, clinic=clinic, role='DOCTOR', status='ACTIVE', joined_at=timezone.now())
        self.member = ClinicMembership.objects.create(user=self.staff, clinic=self.a, role='STAFF', status='ACTIVE', joined_at=timezone.now())
        ClinicMembership.objects.create(user=self.admin, clinic=self.a, role='CLINIC_ADMIN', status='ACTIVE', joined_at=timezone.now())
        self.patient_a = self.patient(self.a, '1111111111')
        self.patient_b = self.patient(self.b, '2222222222')
        self.headers = {'HTTP_X_CLINIC_ID': str(self.a.pk)}
        self.client.force_authenticate(self.doctor)

    def patient(self, clinic, phone):
        return Paciente.objects.create(clinic=clinic, medico=self.doctor, nombre='Prueba', appat='Demo', apmat='Paciente', fecha_nacimiento='1990-01-01', genero='F', telefono=phone, email=f'{phone}@example.test')

    def payload(self, patient=None):
        return {'paciente_id': (patient or self.patient_a).pk, 'fecha': str(timezone.localdate() + timedelta(days=1)), 'hora': '10:00', 'motivo': 'Control'}

    def test_global_clinical_api_closed_even_for_superuser_and_all_methods(self):
        self.client.force_authenticate(User.objects.create_superuser('closure-root', password='synthetic'))
        for path in ('patients/', 'patients.json', 'appointments.json', 'clinical-images/1.json', 'patients/1/email/', 'appointments/1/complete/', 'clinical-images/1/file/', 'consultations/1/', 'diagnostics/', 'exports/patients.xlsx', 'dashboard/'):
            for method in ('get', 'post', 'put', 'patch', 'delete', 'options', 'head'):
                response = getattr(self.client, method)('/api/v1/' + path)
                self.assertEqual(response.status_code, 410, (method, path))
        self.assertEqual(self.client.get(reverse('api-session')).status_code, 200)

    def test_no_new_unassigned_patient_through_service(self):
        from api.services.patients import create_patient
        from rest_framework.exceptions import PermissionDenied
        outsider = User.objects.create_user('no-clinic')
        with self.assertRaises(PermissionDenied):
            create_patient(medico=outsider, validated_data={'nombre': 'X'})

    def test_tenant_contact_checks_owner_context_and_stored_recipient(self):
        url = reverse('tenant-patient-email', args=[self.patient_a.pk])
        body = {'asunto': 'Control', 'mensaje': 'Recordatorio sintético'}
        self.assertEqual(self.client.post(url, body, **self.headers).status_code, 200)
        self.assertEqual(mail.outbox[0].to, [self.patient_a.email])
        self.assertIn(self.a.name, mail.outbox[0].body)
        self.assertTrue(AuditEvent.objects.filter(clinic=self.a, action='TENANT_PATIENT_EMAIL_SENT').exists())
        self.assertEqual(self.client.post(url, {**body, 'email': self.patient_b.email}, **self.headers).status_code, 400)
        self.assertEqual(self.client.post(reverse('tenant-patient-email', args=[self.patient_b.pk]), body, **self.headers).status_code, 404)
        self.client.force_authenticate(self.staff)
        self.assertEqual(self.client.post(url, body, **self.headers).status_code, 403)
        ClinicMembership.objects.filter(user=self.doctor, clinic=self.a).update(status='REVOKED')
        self.client.force_authenticate(self.doctor)
        self.assertEqual(self.client.post(url, body, **self.headers).status_code, 403)
        self.assertEqual(len(mail.outbox), 1)

    @patch('api.tenant_contact.send_patient_email', return_value=0)
    def test_failed_contact_delivery_does_not_record_success(self, _send):
        response = self.client.post(reverse('tenant-patient-email', args=[self.patient_a.pk]), {'asunto': 'Control', 'mensaje': 'Prueba'}, **self.headers)
        self.assertEqual(response.status_code, 503)
        self.assertFalse(AuditEvent.objects.filter(action='TENANT_PATIENT_EMAIL_SENT').exists())

    def test_staff_agenda_is_scoped_and_has_no_clinical_payload(self):
        self.client.force_authenticate(self.staff)
        url = reverse('tenant-staff-appointments')
        created = self.client.post(url, self.payload(), **self.headers)
        self.assertEqual(created.status_code, 201, created.data)
        appointment_id = created.data['id']
        self.assertEqual(set(created.data['patient']), {'id', 'name', 'doctor'})
        self.assertNotIn('observaciones', created.data)
        listed = self.client.get(url, **self.headers)
        self.assertEqual([row['id'] for row in listed.data['results']], [appointment_id])
        self.assertEqual(self.client.post(url, self.payload(self.patient_b), **self.headers).status_code, 404)
        other = Cita.objects.create(paciente=self.patient_b, fecha=self.payload()['fecha'], hora='10:00', motivo='Other')
        foreign_url = reverse('tenant-staff-appointment-detail', args=[other.pk])
        self.assertEqual(self.client.get(foreign_url, **self.headers).status_code, 404)
        self.assertEqual(self.client.patch(foreign_url, {'hora': '12:00'}, **self.headers).status_code, 404)
        self.assertEqual(self.client.post(reverse('tenant-staff-appointment-transition', args=[other.pk, 'cancel']), **self.headers).status_code, 404)
        self.assertEqual(self.client.get(reverse('tenant-medical-history', args=[self.patient_a.pk]), **self.headers).status_code, 403)
        self.assertEqual(self.client.get(reverse('tenant-staff-patients'), **self.headers).data['results'][0]['id'], self.patient_a.pk)
        own = reverse('tenant-staff-appointment-detail', args=[appointment_id])
        self.assertEqual(self.client.patch(own, {'hora': '12:00'}, **self.headers).status_code, 200)
        self.assertEqual(self.client.patch(own, {'clinic_id': str(self.b.pk)}, **self.headers).status_code, 400)
        completed = self.client.post(reverse('tenant-staff-appointment-transition', args=[appointment_id, 'complete']), **self.headers)
        self.assertEqual(completed.status_code, 200)
        self.assertEqual(self.client.post(reverse('tenant-staff-appointment-transition', args=[appointment_id, 'cancel']), **self.headers).status_code, 409)
        self.member.status = 'REVOKED'
        self.member.save()
        self.assertEqual(self.client.get(url, **self.headers).status_code, 403)

    def test_staff_cannot_schedule_for_suspended_doctor_or_inactive_clinic(self):
        self.client.force_authenticate(self.staff)
        ClinicMembership.objects.filter(clinic=self.a, user=self.doctor).update(status='SUSPENDED')
        self.assertEqual(self.client.post(reverse('tenant-staff-appointments'), self.payload(), **self.headers).status_code, 404)
        self.a.status = 'SUSPENDED'
        self.a.save()
        self.assertEqual(self.client.get(reverse('tenant-staff-patients'), **self.headers).status_code, 403)

    def test_doctor_or_clinic_admin_cannot_use_staff_scope(self):
        for account in (self.doctor, self.admin):
            self.client.force_authenticate(account)
            self.assertEqual(self.client.get(reverse('tenant-staff-appointments'), **self.headers).status_code, 403)

    def test_consent_generates_private_pdf_and_cross_clinic_download_is_denied(self):
        from .document_fixtures import publish_documents, evidence_values, signed_pdf_bytes, scan_test_documents
        from Pacientes.models import ConsentEvidence
        _, template = publish_documents(self.a, self.doctor)
        upload = SimpleUploadedFile('identity.pdf', signed_pdf_bytes(), content_type='application/pdf')
        response = self.client.post(reverse('tenant-consent', args=[self.patient_a.pk]), evidence_values(template, upload), format='multipart', **self.headers)
        self.assertEqual(response.status_code, 201, response.data)
        consent = ConsentEvidence.objects.get(patient=self.patient_a)
        self.assertTrue(consent.signed_document.name.startswith(f'tenants/{self.a.pk}/patients/{self.patient_a.pk}/consents/evidence/'))
        url = reverse('consent-evidence-file', args=[self.patient_a.pk, consent.pk])
        self.assertEqual(self.client.get(url, **self.headers).status_code, 423)
        scan_test_documents()
        response = self.client.get(url, **self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b''.join(response.streaming_content).startswith(b'%PDF-'))
        self.assertEqual(self.client.get(url, HTTP_X_CLINIC_ID=str(self.b.pk)).status_code, 404)

    @override_settings(DEBUG=True, ALLOW_LOCAL_HTTP_INVITATIONS=True, TENANT_INVITATION_URL='http://localhost:5173/invitations/accept')
    def test_local_invitation_http_loopback_delivers_and_is_consumed(self):
        self.client.force_authenticate(self.admin)
        user = User.objects.create_user('closure-invited', email='invited@example.test')
        response = self.client.post(reverse('clinic-invitation-create'), {'email': user.email, 'role': 'STAFF'}, **self.headers)
        self.assertEqual(response.status_code, 202)
        token = mail.outbox[0].body.split('#')[1].strip()
        self.client.force_authenticate(user)
        response = self.client.post(reverse('clinic-invitation-resolve'), {'token': token, 'action': 'accept'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(ClinicMembership.objects.filter(user=user, clinic=self.a, role='STAFF', status='ACTIVE').exists())

    def test_http_invitation_never_allowed_in_production_or_remote_hosts(self):
        from api.tenant_views import invitation_delivery_url, InvitationUnavailable
        for debug, allow, url in ((False, True, 'http://localhost:5173/invitations/accept'), (True, False, 'http://localhost:5173/invitations/accept'), (True, True, 'http://example.test/invitations/accept'), (True, True, 'http://localhost.evil.test/invitations/accept'), (True, True, 'http://user@localhost/invitations/accept')):
            with self.subTest(url=url, debug=debug, allow=allow), override_settings(DEBUG=debug, ALLOW_LOCAL_HTTP_INVITATIONS=allow, TENANT_INVITATION_URL=url):
                with self.assertRaises(InvitationUnavailable):
                    invitation_delivery_url()

    def test_read_only_integrity_gate_fails_for_unassigned_data(self):
        call_command('check_tenant_integrity', stdout=StringIO())
        self.patient_a.clinic = None
        self.patient_a.save(update_fields=['clinic'])
        output = StringIO()
        with self.assertRaises(CommandError):
            call_command('check_tenant_integrity', stdout=output)
        self.assertIn('"patients_without_clinic": 1', output.getvalue())
        self.patient_a.refresh_from_db()
        self.assertIsNone(self.patient_a.clinic_id)


from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Event
from django.db import close_old_connections, transaction
from django.test import TransactionTestCase, skipUnlessDBFeature
from rest_framework.test import APIClient


@skipUnlessDBFeature('has_select_for_update')
class StaffConcurrencyTests(TransactionTestCase):
    def setUp(self):
        self.clinic = Clinic.objects.create(name='Race', slug='staff-race', status='ACTIVE')
        self.doctor = User.objects.create_user('staff-race-doctor')
        self.staff = User.objects.create_user('staff-race-staff')
        ClinicMembership.objects.create(user=self.doctor, clinic=self.clinic, role='DOCTOR', status='ACTIVE')
        self.member = ClinicMembership.objects.create(user=self.staff, clinic=self.clinic, role='STAFF', status='ACTIVE')
        self.patient = Paciente.objects.create(clinic=self.clinic, medico=self.doctor, nombre='Prueba', appat='Demo', apmat='Race', fecha_nacimiento='1990-01-01', genero='F', telefono='1234567890', email='race@example.test')

    def request_in_thread(self, username, url, body=None):
        close_old_connections()
        try:
            client = APIClient()
            client.force_authenticate(User.objects.get(username=username))
            return client.post(url, body or {}, format='json', HTTP_X_CLINIC_ID=str(self.clinic.pk)).status_code
        finally:
            close_old_connections()

    def test_staff_and_doctor_transitions_have_one_winner(self):
        appointment = Cita.objects.create(paciente=self.patient, fecha=timezone.localdate()+timedelta(days=1), hora='10:00', motivo='Race')
        barrier = Barrier(2)

        def transition(actor):
            barrier.wait(timeout=10)
            if actor == 'doctor':
                url = reverse('tenant-appointment-transition', args=[appointment.pk, 'complete'])
                return self.request_in_thread(self.doctor.username, url)
            url = reverse('tenant-staff-appointment-transition', args=[appointment.pk, 'cancel'])
            return self.request_in_thread(self.staff.username, url)

        with ThreadPoolExecutor(max_workers=2) as pool:
            statuses = list(pool.map(transition, ('staff', 'doctor')))
        self.assertCountEqual(statuses, [200, 409])

    def test_revoked_staff_cannot_publish_after_waiting_for_clinic_lock(self):
        from api.tenant_context import lock_clinic_capability
        entered = Event()

        def waiting_lock(*args, **kwargs):
            entered.set()
            return lock_clinic_capability(*args, **kwargs)

        body = {'paciente_id': self.patient.pk, 'fecha': str(timezone.localdate()+timedelta(days=1)), 'hora': '10:00', 'motivo': 'Race'}
        with patch('api.tenant_staff.lock_clinic_capability', side_effect=waiting_lock), ThreadPoolExecutor(max_workers=1) as pool:
            with transaction.atomic():
                Clinic.objects.select_for_update().get(pk=self.clinic.pk)
                future = pool.submit(self.request_in_thread, self.staff.username, reverse('tenant-staff-appointments'), body)
                self.assertTrue(entered.wait(10))
                self.member.status = 'REVOKED'
                self.member.save(update_fields=['status'])
            self.assertEqual(future.result(timeout=10), 403)
        self.assertFalse(Cita.objects.exists())

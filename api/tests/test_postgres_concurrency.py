from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from threading import Event
import uuid
from unittest.mock import patch
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files.base import ContentFile
from unittest import skipUnless

from django.contrib.auth.models import User
from django.contrib.auth.models import Permission
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.db import close_old_connections, connection
from django.test import TransactionTestCase
from django.urls import reverse
from rest_framework.test import APIClient
from api.authentication import SessionRefreshToken as RefreshToken

from Usuarios.models import Clinic, ClinicMembership
from api.services.clinical_records import ConcurrentModification, save_record
from api.services.appointments import InvalidStateTransition, transition_appointment
from Citas.models import Cita
from Pacientes.models import AntescedentesMedicos, ClinicalRevision, ImagenesClinicas, Paciente
from DiagnosticosIA.runs import execute
from DiagnosticosIA.models import AIAnalysisRun
from api.services.backoffice import set_user_active
from api.services.password_recovery import confirm_reset, InvalidReset


@skipUnless(connection.vendor == 'postgresql', 'POSTGRESQL CONCURRENCY VERIFICATION REQUIRED')
class PostgreSQLConcurrencyTests(TransactionTestCase):
    def test_two_clinic_sessions_cannot_overwrite_same_clinical_version(self):
        doctor = User.objects.create_user('doctor-clinic-race')
        clinic = Clinic.objects.create(name='Concurrency clinic', slug='concurrency-clinic', status='ACTIVE')
        ClinicMembership.objects.create(user=doctor, clinic=clinic, role='DOCTOR', status='ACTIVE')
        patient = Paciente.objects.create(nombre='A', appat='A', apmat='A', fecha_nacimiento='1990-01-01', genero='F', telefono='1234567890', email='clinic-race@example.test', medico=doctor, clinic=clinic)
        barrier = Barrier(2)

        def update(actor_id):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                try:
                    save_record(user=User.objects.get(pk=actor_id), patient_id=patient.pk, model=AntescedentesMedicos, changes={'alergias': 'sintetico'}, expected_version=0, clinic_id=clinic.pk)
                    return 'saved'
                except ConcurrentModification:
                    return 'conflict'
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(update, [doctor.pk, doctor.pk]))
        self.assertCountEqual(results, ['saved', 'conflict'])
        self.assertEqual(ClinicalRevision.objects.filter(patient=patient, version=1).count(), 1)
        self.assertEqual(AntescedentesMedicos.objects.get(paciente=patient).medico_id, doctor.pk)

    def test_password_reset_wins_against_inflight_session_refresh(self):
        from api.auth_views import _refresh_user
        user = User.objects.create_user('session-reset-race', email='session-race@example.test', password='Old password 123!')
        refresh = str(RefreshToken.for_user(user))
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        checked, release = Event(), Event()

        def delayed_refresh(request):
            result = _refresh_user(request)
            checked.set()
            if not release.wait(10):
                raise TimeoutError('synthetic timeout')
            return result

        def session():
            close_old_connections()
            try:
                client = APIClient()
                client.cookies['smile_refresh'] = refresh
                return client.get(reverse('api-session')).data
            finally:
                close_old_connections()

        with patch('api.auth_views._refresh_user', side_effect=delayed_refresh), ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(session)
            self.assertTrue(checked.wait(10))
            confirm_reset(uid, token, 'New synthetic password 459!', uuid.uuid4())
            release.set()
            self.assertFalse(future.result(timeout=10)['authenticated'])

    def test_password_reset_wins_against_inflight_old_password_login(self):
        from django.contrib.auth import authenticate
        user = User.objects.create_user('login-reset-race', email='race@example.test', password='Old valid password 123!')
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        authenticated, release = Event(), Event()

        def delayed_auth(*args, **kwargs):
            result = authenticate(*args, **kwargs)
            authenticated.set()
            if not release.wait(10):
                raise TimeoutError('synthetic timeout')
            return result

        def login():
            close_old_connections()
            try:
                return APIClient().post(reverse('api-login'), {'username': 'login-reset-race', 'password': 'Old valid password 123!'}, format='json').status_code
            finally:
                close_old_connections()

        with patch('api.auth_views.authenticate', side_effect=delayed_auth), ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(login)
            self.assertTrue(authenticated.wait(10))
            confirm_reset(uid, token, 'New synthetic password 459!', uuid.uuid4())
            release.set()
            self.assertEqual(future.result(timeout=10), 400)

    def test_concurrent_password_reset_only_one_succeeds(self):
        user = User.objects.create_user('reset-race', email='reset-race@example.test', password='old passphrase 123!')
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        barrier = Barrier(2)

        def reset():
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                try:
                    confirm_reset(uid, token, 'New synthetic password 459!', uuid.uuid4())
                    return 'success'
                except InvalidReset:
                    return 'invalid'
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: reset(), range(2)))
        self.assertCountEqual(results, ['success', 'invalid'])
    def test_refresh_racing_deactivation_cannot_survive_reactivation(self):
        actor = User.objects.create_user('admin-concurrency')
        actor.user_permissions.add(Permission.objects.get(content_type__app_label='Usuarios', codename='access_system_backoffice'))
        target = User.objects.create_user('target-concurrency')
        refresh = str(RefreshToken.for_user(target))
        barrier = Barrier(2)

        def deactivate():
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                set_user_active(actor=User.objects.get(pk=actor.pk), user_id=target.pk, active=False, request_id=uuid.uuid4())
            finally:
                close_old_connections()

        def rotate():
            close_old_connections()
            try:
                client = APIClient()
                client.cookies['smile_refresh'] = refresh
                barrier.wait(timeout=10)
                response = client.post(reverse('api-refresh'))
                return response.status_code, response.cookies.get('smile_refresh')
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            first, second = pool.submit(deactivate), pool.submit(rotate)
            first.result(timeout=20)
            code, cookie = second.result(timeout=20)
        self.assertIn(code, (200, 401))
        target.refresh_from_db()
        self.assertFalse(target.is_active)
        set_user_active(actor=actor, user_id=target.pk, active=True, request_id=uuid.uuid4())
        client = APIClient()
        client.cookies['smile_refresh'] = cookie.value if code == 200 else refresh
        self.assertEqual(client.post(reverse('api-refresh')).status_code, 401)

    def test_two_requests_only_run_one_analysis(self):
        user = User.objects.create_user('ai-concurrent')
        patient = Paciente.objects.create(nombre='A', appat='A', apmat='A', fecha_nacimiento='1990-01-01', genero='F', telefono='3333333333', email='c@example.test', medico=user)
        image = ImagenesClinicas.objects.create(paciente=patient, medico=user, tipo_imagen='RX', imagen=SimpleUploadedFile('input.bin', b'synthetic'))
        started, release = Event(), Event()

        def analyzer(item, expected_hash):
            started.set()
            if not release.wait(10):
                raise TimeoutError('synthetic timeout')
            item.resultados.save('result.jpg', ContentFile(b'synthetic'), save=True)
            return []

        def run():
            close_old_connections()
            try:
                return execute(user=User.objects.get(pk=user.pk), image_id=image.pk, request_id=uuid.uuid4(), force=False, analyzer=analyzer)[1]
            finally:
                close_old_connections()

        with patch('DiagnosticosIA.runs.model_version', return_value='a' * 64):
            with ThreadPoolExecutor(max_workers=2) as pool:
                first = pool.submit(run)
                self.assertTrue(started.wait(10))
                second = pool.submit(run)
                self.assertEqual(second.result(timeout=10), 'running')
                release.set()
                self.assertEqual(first.result(timeout=10), 'created')
        self.assertEqual(AIAnalysisRun.objects.count(), 1)
    def test_competing_initial_edits_serialize_and_reject_stale_version(self):
        user = User.objects.create_user('concurrency-user')
        patient = Paciente.objects.create(nombre='A', appat='A', apmat='A', fecha_nacimiento='1990-01-01', genero='F', telefono='1234567890', email='a@example.test', medico=user)
        barrier = Barrier(2)

        def edit(value):
            close_old_connections()
            try:
                actor = User.objects.get(pk=user.pk)
                barrier.wait(timeout=10)
                try:
                    save_record(user=actor, patient_id=patient.pk, model=AntescedentesMedicos, changes={'otros': value}, expected_version=0)
                    return 'success'
                except ConcurrentModification:
                    return 'conflict'
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(edit, ('uno', 'dos')))
        self.assertCountEqual(results, ['success', 'conflict'])
        self.assertEqual(AntescedentesMedicos.objects.filter(paciente=patient).count(), 1)
        self.assertEqual(ClinicalRevision.objects.count(), 1)

    def test_competing_appointment_transitions_have_single_winner(self):
        user = User.objects.create_user('appointment-user')
        patient = Paciente.objects.create(nombre='A', appat='A', apmat='A', fecha_nacimiento='1990-01-01', genero='F', telefono='2222222222', email='b@example.test', medico=user)
        appointment = Cita.objects.create(paciente=patient, fecha='2030-01-01', hora='10:00', motivo='x')
        barrier = Barrier(2)

        def transition(target):
            close_old_connections()
            try:
                row = Cita.objects.get(pk=appointment.pk)
                barrier.wait(timeout=10)
                try:
                    transition_appointment(user=User.objects.get(pk=user.pk), appointment=row, target=target)
                    return 'success'
                except InvalidStateTransition:
                    return 'conflict'
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(transition, ('C', 'A')))
        self.assertCountEqual(results, ['success', 'conflict'])
        appointment.refresh_from_db()
        self.assertIn(appointment.estatus, ('C', 'A'))

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from threading import Event
import uuid
from unittest.mock import patch
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files.base import ContentFile
from unittest import skipUnless

from django.contrib.auth.models import User
from django.db import close_old_connections, connection
from django.test import TransactionTestCase

from api.services.clinical_records import ConcurrentModification, save_record
from api.services.appointments import InvalidStateTransition, transition_appointment
from Citas.models import Cita
from Pacientes.models import AntescedentesMedicos, ClinicalRevision, ImagenesClinicas, Paciente
from DiagnosticosIA.runs import execute
from DiagnosticosIA.models import AIAnalysisRun


@skipUnless(connection.vendor == 'postgresql', 'POSTGRESQL CONCURRENCY VERIFICATION REQUIRED')
class PostgreSQLConcurrencyTests(TransactionTestCase):
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

from datetime import timedelta
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from Citas.models import Cita
from Pacientes.models import AntescedentesMedicos, ClinicalRevision, Odontograma, Paciente
from api.services.appointments import can_transition
from Usuarios.models import AuditEvent


class ClinicalIntegrityTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user('doctor')
        self.patient = Paciente.objects.create(nombre='A', appat='B', apmat='C', fecha_nacimiento='1990-01-01', genero='F', telefono='1234567890', email='a@example.test', medico=self.user)
        self.client.force_authenticate(self.user)

    def test_appointment_patch_preserves_omitted_values_and_null(self):
        appointment = Cita.objects.create(paciente=self.patient, fecha=timezone.localdate()+timedelta(days=1), hora='10:00', motivo='Motivo', estatus='P', observaciones='Nota')
        url = reverse('api-appointment-detail', args=[appointment.pk])
        response = self.client.patch(url, {'hora': '11:00'}, format='json')
        self.assertEqual(response.status_code, 200)
        appointment.refresh_from_db()
        self.assertEqual((appointment.motivo, appointment.estatus, appointment.observaciones), ('Motivo', 'P', 'Nota'))
        response = self.client.patch(url, {'observaciones': None}, format='json')
        self.assertEqual(response.status_code, 200)
        appointment.refresh_from_db()
        self.assertIsNone(appointment.observaciones)

    def test_transition_matrix(self):
        for current in 'PCA':
            for target in 'PCA':
                with self.subTest(current=current, target=target):
                    self.assertEqual(can_transition(current, target), current == target or (current == 'P' and target in 'CA'))
        self.assertFalse(can_transition('X', 'P'))

    def test_transition_matrix_through_patch(self):
        for current in 'PCA':
            for target in 'PCA':
                with self.subTest(current=current, target=target):
                    appointment = Cita.objects.create(paciente=self.patient, fecha=timezone.localdate()+timedelta(days=1), hora='10:00', motivo='x', estatus=current)
                    response = self.client.patch(reverse('api-appointment-detail', args=[appointment.pk]), {'estatus': target}, format='json')
                    self.assertEqual(response.status_code, 200 if can_transition(current, target) else 409)
                    appointment.refresh_from_db()
                    self.assertEqual(appointment.estatus, target if can_transition(current, target) else current)

    def test_medical_history_revisions_and_optimistic_conflict(self):
        url = reverse('api-medical-history', args=[self.patient.pk])
        first = self.client.put(url, {'version': 0, 'otros': 'primero'}, format='json')
        self.assertEqual(first.status_code, 200, first.data)
        second = self.client.put(url, {'version': 1, 'otros': 'segundo'}, format='json')
        self.assertEqual(second.status_code, 200, second.data)
        stale = self.client.put(url, {'version': 1, 'otros': 'perdido'}, format='json')
        self.assertEqual(stale.status_code, 409)
        history = AntescedentesMedicos.objects.get(paciente=self.patient)
        self.assertEqual((history.otros, history.version), ('segundo', 2))
        versions = ClinicalRevision.objects.filter(resource_type='medical_history').order_by('version')
        self.assertEqual([v.snapshot['otros'] for v in versions], ['primero', 'segundo'])
        self.assertEqual(AuditEvent.objects.filter(action='CLINICAL_HISTORY_UPDATE').count(), 2)

    def test_odontogram_revisions_conflicts_and_validation(self):
        url = reverse('api-odontogram', args=[self.patient.pk])
        payload = {'version': 0, 'denticion_permanente': {'11': {'oclusal': 'caries'}}, 'denticion_decidua': {}, 'resumen': {}}
        self.assertEqual(self.client.put(url, payload, format='json').status_code, 200)
        self.assertEqual(self.client.put(url, payload, format='json').status_code, 409)
        payload['version'] = 1
        payload['denticion_permanente']['11']['oclusal'] = 'restauracion'
        self.assertEqual(self.client.put(url, payload, format='json').status_code, 200)
        revisions = ClinicalRevision.objects.filter(resource_type='odontogram').order_by('version')
        self.assertEqual([r.snapshot['dientes_permanentes']['11']['oclusal'] for r in revisions], ['caries', 'restauracion'])
        payload['version'] = 2
        payload['denticion_permanente'] = {'99': {'oclusal': 'sano'}}
        self.assertEqual(self.client.put(url, payload, format='json').status_code, 400)
        self.assertEqual(Odontograma.objects.get(paciente=self.patient).version, 2)

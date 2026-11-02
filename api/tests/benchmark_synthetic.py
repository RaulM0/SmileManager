"""Medición opt-in; únicamente ejecutable en la DB PostgreSQL temporal de tests."""
import json
import time
import tracemalloc
from datetime import timedelta

from django.contrib.auth.models import User
from django.db import connection
from django.test import TransactionTestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from Citas.models import Cita
from Pacientes.models import Consulta, ImagenesClinicas, Paciente


class SyntheticBaseline(TransactionTestCase):
    def test_baseline(self):
        if connection.vendor != 'postgresql' or not connection.settings_dict['NAME'].startswith('test_smile_phase2_'):
            self.skipTest('Requiere DB PostgreSQL temporal aislada.')
        owner = User.objects.create_user(username='synthetic-benchmark')
        client = APIClient()
        client.force_authenticate(owner)
        patient = None
        previous = 0
        report = []
        for n in (10, 100, 1000):
            batch = [Paciente(nombre='Synthetic', appat='Patient', apmat='Test', fecha_nacimiento='1990-01-01', genero='F', telefono=f'{i:010d}', email=f'synthetic-{i}@example.test', medico=owner) for i in range(previous, n)]
            Paciente.objects.bulk_create(batch)
            patients = list(Paciente.objects.filter(medico=owner).order_by('id'))
            patient = patients[0]
            Cita.objects.bulk_create([Cita(paciente=p, fecha=timezone.localdate()+timedelta(days=1), hora='10:00', motivo='Synthetic') for p in patients[previous:n]])
            Consulta.objects.bulk_create([Consulta(paciente=patient, medico=owner, fecha_consulta=timezone.now(), motivo_consulta='Synthetic') for _ in range(n-previous)])
            consult = Consulta.objects.filter(paciente=patient).first()
            ImagenesClinicas.objects.bulk_create([ImagenesClinicas(paciente=patient, medico=owner, consulta=consult, tipo_imagen='RX', descripcion='Synthetic', imagen='synthetic/placeholder.png') for _ in range(n-previous)])
            endpoints = {
                'dashboard': reverse('api-dashboard'), 'patients': reverse('api-patient-list'),
                'search': reverse('api-patient-list')+'?search=Synthetic', 'autocomplete': reverse('api-patient-autocomplete')+'?term=Synthetic',
                'patient': reverse('api-patient-detail', args=[patient.pk]), 'history': reverse('api-medical-history', args=[patient.pk]),
                'consultations': reverse('api-consultations', args=[patient.pk]), 'appointments': reverse('api-appointment-list'),
                'odontogram': reverse('api-odontogram', args=[patient.pk]), 'images': reverse('api-clinical-images', args=[patient.pk]),
                'diagnostics': reverse('api-diagnostics'), 'consent': reverse('api-consent', args=[patient.pk]),
                'study': reverse('api-comparative-study', args=[patient.pk]), 'export_patients': reverse('api-export-patients'),
            }
            for name, url in endpoints.items():
                tracemalloc.start()
                start = time.perf_counter()
                with CaptureQueriesContext(connection) as queries:
                    response = client.get(url)
                    payload = len(response.content)
                elapsed = (time.perf_counter()-start)*1000
                _, peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()
                self.assertEqual(response.status_code, 200, name)
                report.append({'n': n, 'endpoint': name, 'queries': len(queries), 'db_ms': round(sum(float(q['time']) for q in queries)*1000, 2), 'total_ms': round(elapsed, 2), 'bytes': payload, 'peak_py_bytes': peak})
            previous = n
        print('SYNTHETIC_BENCHMARK=' + json.dumps(report))
        print('SYNTHETIC_EXPLAIN_SEARCH=' + Paciente.objects.filter(medico=owner, nombre__icontains='Synthetic').explain(analyze=True, buffers=True, format='text').replace('\n', ' | '))
        print('SYNTHETIC_EXPLAIN_APPOINTMENTS=' + Cita.objects.filter(paciente__medico=owner, fecha__gt=timezone.localdate()).order_by('fecha', 'hora').explain(analyze=True, buffers=True, format='text').replace('\n', ' | '))

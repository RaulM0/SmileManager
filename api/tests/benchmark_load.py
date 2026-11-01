"""Carga secuencial y local de APIClient; no mide red ni producción."""
import json
import statistics
import time
from datetime import timedelta

import psutil
from django.contrib.auth.models import User
from django.db import connection
from django.test import TransactionTestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from Citas.models import Cita
from Pacientes.models import Paciente


class SyntheticLoad(TransactionTestCase):
    def test_load(self):
        if connection.vendor != 'postgresql' or not connection.settings_dict['NAME'].startswith('test_smile_phase2_'):
            self.skipTest('Solo PostgreSQL temporal.')
        user = User.objects.create_user('synthetic-load')
        Paciente.objects.bulk_create([Paciente(nombre='Synthetic', appat='Test', apmat='Patient', fecha_nacimiento='1990-01-01', genero='F', telefono=f'{i:010d}', email=f'x{i}@example.test', medico=user) for i in range(1000)], batch_size=500)
        patient = Paciente.objects.filter(medico=user).first()
        Cita.objects.bulk_create([Cita(paciente=patient, fecha=timezone.localdate()+timedelta(days=1), hora='10:00', motivo='Synthetic') for _ in range(100)])
        routes = {'patients': reverse('api-patient-list'), 'agenda': reverse('api-appointment-list'), 'record': reverse('api-medical-history', args=[patient.pk]), 'search': reverse('api-patient-list')+'?search=Synthetic'}
        client = APIClient()
        client.force_authenticate(user)
        process = psutil.Process()
        results = {}
        for label, url in routes.items():
            samples = []
            errors = 0
            cpu = time.process_time()
            wall = time.perf_counter()
            for _ in range(50):
                start = time.perf_counter()
                response = client.get(url)
                samples.append((time.perf_counter()-start)*1000)
                errors += response.status_code != 200
            elapsed = time.perf_counter()-wall
            results[label] = {'samples': len(samples), 'rps_in_process': round(len(samples)/elapsed, 2), 'p50_ms': round(statistics.median(samples), 2), 'p95_ms': round(sorted(samples)[47], 2), 'errors': errors, 'cpu_seconds': round(time.process_time()-cpu, 2), 'rss_bytes_after': process.memory_info().rss}
        print('SYNTHETIC_LOAD=' + json.dumps(results))

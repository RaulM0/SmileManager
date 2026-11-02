import json
import time
import tracemalloc

from django.contrib.auth.models import User
from django.db import connection
from django.test import TransactionTestCase, override_settings
from django.test.utils import CaptureQueriesContext
from api.services.exports import export_patients
from Pacientes.models import Paciente


class ExportBenchmark(TransactionTestCase):
    @override_settings(EXPORT_MAX_ROWS=10000)
    def test_export(self):
        if connection.vendor != 'postgresql' or not connection.settings_dict['NAME'].startswith('test_smile_phase2_'):
            self.skipTest('Solo PostgreSQL temporal.')
        owner = User.objects.create_user('synthetic-export')
        previous = 0
        results = []
        for n in (100, 1000, 10000):
            Paciente.objects.bulk_create([Paciente(nombre='Synthetic', appat='Test', apmat='Patient', fecha_nacimiento='1990-01-01', genero='F', telefono=f'{i:010d}', email=f'patient-{i}@example.test', medico=owner) for i in range(previous, n)], batch_size=500)
            tracemalloc.start()
            start = time.perf_counter()
            with CaptureQueriesContext(connection) as queries:
                response = export_patients(owner)
            seconds = time.perf_counter()-start
            _, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            results.append({'n': n, 'seconds': round(seconds, 3), 'queries': len(queries), 'xlsx_bytes': len(response.content), 'peak_python_bytes': peak})
            previous = n
        print('SYNTHETIC_EXPORT=' + json.dumps(results))

"""Loopback HTTP real con datos y base temporales; no mide producción."""
import concurrent.futures
import json
import statistics
import time
from datetime import timedelta
from threading import Event, Thread

import requests
from django.contrib.auth.models import User
from django.db import close_old_connections, connection
from django.test import LiveServerTestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken
from Citas.models import Cita
from Pacientes.models import Consulta, ImagenesClinicas, Paciente


class LocalHTTPBenchmark(LiveServerTestCase):
    def test_loopback(self):
        if connection.vendor != 'postgresql' or not connection.settings_dict['NAME'].startswith('test_smile_phase2_'):
            self.skipTest('Solo PostgreSQL temporal.')
        user = User.objects.create_user('http-benchmark')
        patient = Paciente.objects.create(nombre='Synthetic', appat='A', apmat='B', fecha_nacimiento='1990-01-01', genero='F', telefono='1234567890', email='a@example.test', medico=user)
        Cita.objects.bulk_create([Cita(paciente=patient, fecha=timezone.localdate()+timedelta(days=1), hora='10:00', motivo='Synthetic') for _ in range(100)])
        Consulta.objects.bulk_create([Consulta(paciente=patient, medico=user, fecha_consulta=timezone.now(), motivo_consulta='Synthetic') for _ in range(100)])
        consultation = Consulta.objects.filter(paciente=patient).first()
        ImagenesClinicas.objects.bulk_create([ImagenesClinicas(paciente=patient, medico=user, consulta=consultation, tipo_imagen='RX', imagen='synthetic/a.png') for _ in range(100)])
        headers = {'Authorization': 'Bearer ' + str(RefreshToken.for_user(user).access_token)}
        routes = {'patients': reverse('api-patient-list'), 'agenda': reverse('api-appointment-list'), 'consultations': reverse('api-consultations', args=[patient.pk]), 'images': reverse('api-clinical-images', args=[patient.pk])}
        results = []
        peak_connections = [0]
        stop = Event()

        def monitor():
            close_old_connections()
            try:
                while not stop.wait(0.05):
                    with connection.cursor() as cursor:
                        cursor.execute('SELECT count(*) FROM pg_stat_activity WHERE datname = current_database()')
                        peak_connections[0] = max(peak_connections[0], cursor.fetchone()[0])
            finally:
                close_old_connections()

        thread = Thread(target=monitor, daemon=True)
        thread.start()
        try:
            for label, path in routes.items():
                for concurrency in (1, 5, 10):
                    def request_one(_):
                        start = time.perf_counter()
                        try:
                            response = requests.get(self.live_server_url + path, headers=headers, timeout=15)
                            return (time.perf_counter()-start)*1000, response.status_code
                        except requests.RequestException:
                            return (time.perf_counter()-start)*1000, 0
                    start = time.perf_counter()
                    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as pool:
                        rows = list(pool.map(request_one, range(concurrency * 5)))
                    elapsed = time.perf_counter()-start
                    samples = sorted(ms for ms, _ in rows)
                    results.append({'route': label, 'clients': concurrency, 'n': len(rows), 'rps': round(len(rows)/elapsed, 2), 'p50_ms': round(statistics.median(samples), 2), 'p95_ms': round(samples[int((len(samples)-1)*.95)], 2), 'errors': sum(status != 200 for _, status in rows)})
        finally:
            stop.set()
            thread.join()
        print('LOCAL_HTTP=' + json.dumps({'results': results, 'peak_db_connections_observed': peak_connections[0]}))

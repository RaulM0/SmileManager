"""Ejecuta mediciones sintéticas en base PostgreSQL de prueba aleatoria."""
import os
import subprocess
import sys
from urllib.parse import quote
import yaml

with open('compose.yaml', encoding='utf-8') as source:
    config = yaml.safe_load(source)['services']['db']['environment']
user = quote(str(config['POSTGRES_USER']), safe='')
password = quote(str(config['POSTGRES_PASSWORD']), safe='')
env = os.environ.copy()
env.update(PHASE2_TEST_DATABASE_URL=f'postgresql://{user}:{password}@127.0.0.1:5433/postgres', DJANGO_SETTINGS_MODULE='SmileManager.settings_postgres_test', PYTHONDONTWRITEBYTECODE='1')
label = sys.argv[1] if len(sys.argv) > 1 else 'api.tests.benchmark_synthetic'
if label not in ('api.tests.benchmark_synthetic', 'api.tests.benchmark_exports', 'api.tests.benchmark_load', 'api.tests.benchmark_http'):
    raise SystemExit('Solo se permiten los perfiles sintéticos conocidos.')
sys.exit(subprocess.call([sys.executable, '-B', 'manage.py', 'test', label, '--noinput'], env=env))

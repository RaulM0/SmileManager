"""Lanza solo tests de concurrencia contra una DB temporal generada por Django."""
import os
import subprocess
import sys
from urllib.parse import quote
import yaml

with open('compose.yaml', encoding='utf-8') as source:
    env = yaml.safe_load(source)['services']['db']['environment']
user = quote(str(env['POSTGRES_USER']), safe='')
password = quote(str(env['POSTGRES_PASSWORD']), safe='')
test_env = os.environ.copy()
test_env['PHASE2_TEST_DATABASE_URL'] = f'postgresql://{user}:{password}@127.0.0.1:5433/postgres'
test_env['DJANGO_SETTINGS_MODULE'] = 'SmileManager.settings_postgres_test'
test_env['PYTHONDONTWRITEBYTECODE'] = '1'
sys.exit(subprocess.call([sys.executable, '-B', 'manage.py', 'test', 'api.tests.test_postgres_concurrency', '--noinput'], env=test_env))

"""PostgreSQL de pruebas: la base creada lleva un nombre aleatorio exclusivo."""
import os
import uuid
import dj_database_url

from .settings_test import *  # noqa: F403

url = os.environ.get('PHASE2_TEST_DATABASE_URL')
if not url:
    raise RuntimeError('PHASE2_TEST_DATABASE_URL es obligatorio para pruebas PostgreSQL aisladas.')
config = dj_database_url.parse(url)
if config['ENGINE'] != 'django.db.backends.postgresql' or config['NAME'] != 'postgres':
    raise RuntimeError('La conexión de mantenimiento debe apuntar exclusivamente a postgres.')
config['TEST'] = {'NAME': 'test_smile_phase2_' + uuid.uuid4().hex[:20]}
DATABASES = {'default': config}

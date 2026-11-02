"""Pruebas aisladas: nunca conecta a la base ni al storage de desarrollo."""
import tempfile

from .settings_local import *  # noqa: F403

DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
_test_media = tempfile.TemporaryDirectory(prefix='smilemanager-test-media-')
MEDIA_ROOT = _test_media.name
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
LOGGING['loggers']['smile.access']['level'] = 'WARNING'  # noqa: F405

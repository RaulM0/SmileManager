"""Pruebas aisladas: nunca conecta a la base ni al storage de desarrollo."""
import tempfile

from .settings_local import *  # noqa: F403

DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
_test_media = tempfile.TemporaryDirectory(prefix='smilemanager-test-media-')
MEDIA_ROOT = _test_media.name
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
# Exercise historical contracts separately from the default closed boundary.
LEGACY_CLINICAL_API_ENABLED = True
LOGGING['loggers']['smile.access']['level'] = 'WARNING'  # noqa: F405

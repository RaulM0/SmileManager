"""Isolated settings used by the browser parity suite."""

from .settings_local import *  # noqa: F403

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / '.e2e.sqlite3',  # noqa: F405
    }
}
MEDIA_ROOT = BASE_DIR / '.e2e-media'  # noqa: F405
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']

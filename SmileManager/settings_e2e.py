"""Isolated settings used by the browser parity suite."""

from .settings_local import *  # noqa: F403
import os
from pathlib import Path

_e2e_root = os.environ.get('SMILE_E2E_DIR')
if not _e2e_root:
    raise RuntimeError('SMILE_E2E_DIR es obligatorio para pruebas E2E aisladas')
_e2e_root = Path(_e2e_root).resolve()
if _e2e_root.parent != BASE_DIR.resolve() or not _e2e_root.name.startswith('.e2e-run-'):  # noqa: F405
    raise RuntimeError('Directorio E2E inválido')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': _e2e_root / 'test.sqlite3',
    }
}
MEDIA_ROOT = _e2e_root / 'media'
EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
EMAIL_FILE_PATH = _e2e_root / 'mail'
FRONTEND_URL = 'http://127.0.0.1:8010/app'
DEFAULT_FROM_EMAIL = 'smile-e2e@example.test'
TENANT_INVITATION_URL = 'http://127.0.0.1:8010/app/invitations/accept'
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
# Browser parity exercises many independent screens in one isolated process.
# Rate limiting itself is tested separately with explicit low limits.
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {key: '10000/min' for key in REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']}  # noqa: F405

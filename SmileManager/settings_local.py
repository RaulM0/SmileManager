import os

import dj_database_url

# Evita que la configuración base intente construir una base vacía antes de
# sustituirla por la configuración local de PostgreSQL.
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql://smilemanager:smilemanager_local@127.0.0.1:5433/smilemanager",
)

from .settings import *


DEBUG = True
ALLOW_LOCAL_HTTP_INVITATIONS = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

DATABASES = {
    "default": dj_database_url.parse(
        os.environ["DATABASE_URL"],
        conn_max_age=60,
    )
}

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

# Local mail stays in files unless real delivery is deliberately enabled.
# Production uses the SMTP configuration in settings.py independently.
DEV_EMAIL_DELIVERY = os.environ.get('DEV_EMAIL_DELIVERY', 'file').strip().lower()
if DEV_EMAIL_DELIVERY == 'file':
    EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
    EMAIL_FILE_PATH = os.environ.get('DEV_EMAIL_DIR', str(BASE_DIR / '.local-mail'))
elif DEV_EMAIL_DELIVERY == 'smtp':
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
else:
    raise ImproperlyConfigured('DEV_EMAIL_DELIVERY debe ser file o smtp.')

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0

import os

import dj_database_url

# Evita que la configuración base intente construir una base vacía antes de
# sustituirla por la configuración local de PostgreSQL.
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql://smilemanager:smilemanager_local@localhost:5432/smilemanager",
)

from .settings import *


DEBUG = True
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

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False

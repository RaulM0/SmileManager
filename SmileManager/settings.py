# Produccion
import os
from datetime import timedelta
from pathlib import Path
import dj_database_url
from botocore.config import Config
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY
_local_settings = os.environ.get('DJANGO_SETTINGS_MODULE') in ('SmileManager.settings_local', 'SmileManager.settings_e2e', 'SmileManager.settings_test', 'SmileManager.settings_postgres_test')
SECRET_KEY = os.environ.get('SECRET_KEY', '' if not _local_settings else 'local-development-only-not-for-production')
DEBUG = os.environ.get('DJANGO_DEBUG', 'False') == 'True'
ALLOWED_HOSTS = [host.strip() for host in os.environ.get('ALLOWED_HOSTS', '').split(',') if host.strip()]
if not _local_settings:
    if not SECRET_KEY or not ALLOWED_HOSTS or '*' in ALLOWED_HOSTS:
        raise ImproperlyConfigured('Producción requiere SECRET_KEY y ALLOWED_HOSTS explícitos.')
    if DEBUG:
        raise ImproperlyConfigured('DEBUG no está permitido con la configuración de producción.')

# Applications
INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt.token_blacklist',
    'storages',
    'api',
    'Pacientes',
    'Citas',
    'DiagnosticosIA',
    'Usuarios.apps.UsuariosConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'api.observability.RequestLogMiddleware',
    'api.audit.AuditMiddleware',
]

ROOT_URLCONF = 'SmileManager.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'frontend' / 'dist'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'SmileManager.wsgi.application'

# DATABASE
DATABASES = {
    'default': dj_database_url.config(default=os.environ.get('DATABASE_URL'))
}
if DATABASES['default'].get('ENGINE') == 'django.db.backends.postgresql':
    DATABASES['default'].setdefault('OPTIONS', {}).setdefault('connect_timeout', int(os.environ.get('DB_CONNECT_TIMEOUT', '10')))

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Localization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'America/Mexico_City'
USE_I18N = True
USE_TZ = True

# STATIC (WhiteNoise)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    ('react', BASE_DIR / 'frontend' / 'dist'),
]

# ============================================
# AWS S3 Configuration
# ============================================
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
if not _local_settings and (not os.environ.get('DATABASE_URL') or not AWS_STORAGE_BUCKET_NAME):
    raise ImproperlyConfigured('Producción requiere DATABASE_URL y AWS_STORAGE_BUCKET_NAME.')
AWS_S3_REGION_NAME = 'us-east-2'
AWS_S3_CLIENT_CONFIG = Config(connect_timeout=int(os.environ.get('S3_CONNECT_TIMEOUT', '10')), read_timeout=int(os.environ.get('S3_READ_TIMEOUT', '60')))
CLINICAL_UPLOAD_MAX_BYTES = int(os.environ.get('CLINICAL_UPLOAD_MAX_BYTES', str(5 * 1024 * 1024)))
CLINICAL_UPLOAD_MAX_PIXELS = int(os.environ.get('CLINICAL_UPLOAD_MAX_PIXELS', '20000000'))
DASHBOARD_APPOINTMENT_LIMIT = max(1, int(os.environ.get('DASHBOARD_APPOINTMENT_LIMIT', '50')))
EXPORT_MAX_ROWS = max(1, int(os.environ.get('EXPORT_MAX_ROWS', '1000')))
CLINICAL_PAGE_SIZE = max(1, int(os.environ.get('CLINICAL_PAGE_SIZE', '20')))
CLINICAL_MAX_PAGE_SIZE = max(CLINICAL_PAGE_SIZE, int(os.environ.get('CLINICAL_MAX_PAGE_SIZE', '100')))
APPOINTMENT_MAX_RANGE_DAYS = max(1, int(os.environ.get('APPOINTMENT_MAX_RANGE_DAYS', '62')))
BACKOFFICE_AI_STALE_SECONDS = max(1, int(os.environ.get('BACKOFFICE_AI_STALE_SECONDS', '3600')))

# Dominio S3
AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'

# Configuración de objetos
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',
}

# Desactivar ACLs (usar bucket policy en su lugar)
AWS_DEFAULT_ACL = None
AWS_QUERYSTRING_AUTH = True

# URL pública de media
MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/'

# ============================================
# STORAGES - Configuración moderna de Django
# ============================================
STORAGES = {
    # Archivos subidos por usuarios (media) → S3
    "default": {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
    },
    # Archivos estáticos (CSS, JS) → WhiteNoise
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

# Default primary key
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Email
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'true').lower() == 'true'
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_TIMEOUT = int(os.environ.get('SMTP_TIMEOUT', '30'))
EMAIL_HOST_USER = os.environ.get('EMAIL_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_PASS', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER or 'webmaster@localhost')
TENANT_INVITATION_URL = os.environ.get('TENANT_INVITATION_URL', '')
FRONTEND_URL = os.environ.get('FRONTEND_URL', '')
PASSWORD_RESET_TIMEOUT = max(1, int(os.environ.get('PASSWORD_RESET_TIMEOUT', '1800')))

# Session
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_AGE = 1800

# Login
LOGIN_URL = '/app/login'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'authentication': os.environ.get('THROTTLE_AUTH', '30/min'),
        'authentication_account': os.environ.get('THROTTLE_ACCOUNT', '10/min'),
        'password_reset_ip': os.environ.get('THROTTLE_PASSWORD_RESET_IP', '10/hour'),
        'password_reset_account': os.environ.get('THROTTLE_PASSWORD_RESET_ACCOUNT', '3/hour'),
        'password_reset_confirm': os.environ.get('THROTTLE_PASSWORD_RESET_CONFIRM', '20/hour'),
        'expensive': os.environ.get('THROTTLE_EXPENSIVE', '10/min'),
        'email': os.environ.get('THROTTLE_EMAIL', '10/min'),
        'export': os.environ.get('THROTTLE_EXPORT', '10/min'),
    },
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=5),
    'REFRESH_TOKEN_LIFETIME': timedelta(hours=8),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# CSRF & Cookies
CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in os.environ.get('CSRF_TRUSTED_ORIGINS', '').split(',') if origin.strip()]
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_SAMESITE = 'Lax'
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'same-origin'
X_FRAME_OPTIONS = 'DENY'
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {'console': {'class': 'logging.StreamHandler'}},
    'loggers': {'smile.access': {'handlers': ['console'], 'level': os.environ.get('REQUEST_LOG_LEVEL', 'INFO'), 'propagate': False}},
}
# Solo habilitar cuando el proxy confiable elimine y establezca este encabezado.
if os.environ.get('TRUST_PROXY_HTTPS_HEADER') == 'true':
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

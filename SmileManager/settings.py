"""
Django settings for SmileManager project.
...
"""
import os
from pathlib import Path
import dj_database_url
# Asegúrate de instalar dj-database-url, django-storages y boto3
# pip install dj-database-url django-storages boto3

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# --- Configuración de Seguridad y Entorno (Mantenida) ---

# SECRET_KEY se lee de las variables de entorno de EB
SECRET_KEY = os.environ.get('SECRET_KEY','mi_clave_secreta_de_desarollo')

# DEBUG se establece a False en producción por la variable DJANGO_DEBUG=False
DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'

# ALLOWED_HOSTS se lee de las variables de entorno de EB
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '*').split(',')


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # --- Añadimos django-storages para S3 ---
    'storages',
    
    'Home',
    'Pacientes',
    'Citas',
    'DiagnosticosIA',
    'Sesiones',
]

MIDDLEWARE = [
# ... (Middleware sin cambios, el código es el mismo)
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'Sesiones.middleware.LoginRequiredMiddleware',  # Middleware personalizado para requerir login
]


ROOT_URLCONF = 'SmileManager.urls'

TEMPLATES = [
# ... (Templates sin cambios)
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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


# --- Database (ADAPTADO para RDS con dj_database_url) ---
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    # 1. Producción (Elastic Beanstalk/RDS)
    # Usa la variable de entorno DATABASE_URL (se la pasaremos a EB)
    DATABASES = {
        'default': dj_database_url.config(default=DATABASE_URL, conn_max_age=600, ssl_require=False)
    }
else:
    # 2. Desarrollo (Tu configuración local original)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'Dentistas',
            'USER': 'postgres',
            'PASSWORD': '2403', # ¡Cuidado con esta contraseña en local!
            'HOST': '127.0.0.1',
            'PORT' : '5432'
        }
    }


# Password validation
# ... (Sin cambios)
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# ... (Sin cambios)
LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'America/Mexico_City'

USE_I18N = True

USE_TZ = True


# --- Static and Media Files (ADAPTADO para S3) ---

if not DEBUG:
    # --- Configuración S3 (Producción) ---
    
    # Credenciales leídas desde EB
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME')
    
    # Dominio para URLs
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
    
    # Archivos Estáticos (CSS/JS)
    STATICFILES_STORAGE = 'storages.backends.s3boto3.S3StaticStorage'
    STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/static/'
    
    # Archivos Media (Imágenes/YOLO)
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'
    
    # DIRECTORIO TEMPORAL para que YOLO escriba en la instancia EC2 antes de subir a S3
    MEDIA_ROOT = Path('/tmp/media/') 

else:
    # --- Configuración Local (Desarrollo) ---
    STATIC_URL = 'static/'
    MEDIA_URL = '/media/'
    MEDIA_ROOT = BASE_DIR / 'media'


# Default primary key field type
# ... (Sin cambios)
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Email (Sin cambios)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_USE_TLS = True
EMAIL_PORT = 587
EMAIL_HOST_USER = 'raumillandesa@gmail.com'
EMAIL_HOST_PASSWORD = 'peamhxmwuwoejjlr' 


# Configuración de URLs de autenticación (Sin cambios)
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'login'

# Configuración de sesión (Sin cambios)
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_AGE = 1800  # 30 minutos
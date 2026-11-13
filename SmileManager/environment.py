"""Load private CLI env files without overriding deployment environment values."""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent


def load_environment(root=ROOT):
    # Test settings must never pick up the linked cloud database or credentials.
    if os.environ.get('DJANGO_SETTINGS_MODULE', '').endswith(('_test', '_e2e')):
        return
    load_dotenv(root / '.env.local', override=False, interpolate=False)
    load_dotenv(root / '.env', override=False, interpolate=False)


def database_url():
    if len(sys.argv) > 1 and sys.argv[1] == 'migrate':
        return os.environ.get('DATABASE_URL_UNPOOLED') or os.environ.get('DATABASE_URL')
    return os.environ.get('DATABASE_URL')


def configure_postgres(database):
    if database.get('ENGINE') == 'django.db.backends.postgresql':
        database['CONN_HEALTH_CHECKS'] = True
        # PgBouncer transaction pooling cannot preserve named cursors across requests.
        if '-pooler.' in database.get('HOST', ''):
            database['DISABLE_SERVER_SIDE_CURSORS'] = True
    return database

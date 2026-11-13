"""Exercise Django against the linked Neon DB with a synthetic login, deactivated after verification."""
import argparse
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import threading
from urllib.request import Request, urlopen
from wsgiref.simple_server import make_server

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--migrate', action='store_true', help='Apply Django migrations using DATABASE_URL_UNPOOLED.')
    arguments = parser.parse_args()
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SmileManager.settings_local')
    from SmileManager.environment import load_environment
    load_environment()
    if arguments.migrate:
        subprocess.run([sys.executable, 'manage.py', 'migrate', '--noinput'], cwd=ROOT, check=True)

    import django
    django.setup()
    from django.conf import settings
    from django.contrib.auth import get_user_model
    from django.core.wsgi import get_wsgi_application
    from django.db import connection

    host = settings.DATABASES['default'].get('HOST', '')
    if not host.endswith('.neon.tech'):
        raise SystemExit('Refusing cloud verification: database is not hosted on Neon.')
    with connection.cursor() as cursor:
        cursor.execute('SELECT 1')
        assert cursor.fetchone() == (1,)
    print('PASS: Django connected to Neon PostgreSQL.', flush=True)

    username = 'neon-smoke-' + secrets.token_hex(8)
    password = secrets.token_urlsafe(32)
    user = get_user_model().objects.create_user(username=username, password=password)
    server = None
    thread = None
    try:
        assert get_user_model().objects.get(pk=user.pk).username == username
        print('PASS: ORM write/read on Neon with synthetic user.', flush=True)
        server = make_server('127.0.0.1', 0, get_wsgi_application())
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        origin = f'http://127.0.0.1:{server.server_port}'
        for path in ('/health/ready/', '/app/'):
            with urlopen(origin + path, timeout=30) as response:
                assert response.status == 200
                if path.startswith('/health'):
                    assert json.load(response)['status'] == 'ok'
                else:
                    assert b'<html' in response.read().lower()
            print(f'PASS: HTTP GET {path} -> 200.', flush=True)
        request = Request(origin + '/api/v1/auth/login/',
                          data=json.dumps({'username': username, 'password': password}).encode(),
                          headers={'Content-Type': 'application/json', 'Origin': 'http://localhost:8000'})
        with urlopen(request, timeout=30) as response:
            payload = json.load(response)
            assert response.status == 200 and payload['authenticated'] is True
            assert payload['user']['username'] == username
        print('PASS: HTTP login authenticated against Neon -> 200.', flush=True)
    finally:
        if server:
            server.shutdown()
            server.server_close()
        if thread:
            thread.join(timeout=5)
        # Login produces immutable audit events; retain their actor reference.
        user.is_active = False
        user.set_unusable_password()
        user.save(update_fields=['is_active', 'password'])
        print('PASS: synthetic user deactivated; immutable audit preserved.', flush=True)
        connection.close()


if __name__ == '__main__':
    main()

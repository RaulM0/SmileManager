"""Check container startup routing without connecting to a database."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


class DockerEntrypointTests(unittest.TestCase):
    def trace(self, *arguments):
        with tempfile.TemporaryDirectory(prefix='smile-entrypoint-') as temporary:
            directory = Path(temporary)
            for name in ('python', 'gunicorn'):
                executable = directory / name
                executable.write_text('#!/bin/sh\nprintf "%s\\n" "' + name + ' $*" >> "$ENTRYPOINT_TRACE"\n')
                executable.chmod(0o755)
            environment = {**os.environ, 'PATH': str(directory) + ':' + os.environ['PATH'],
                           'ENTRYPOINT_TRACE': str(directory / 'trace')}
            subprocess.run(['sh', str(ROOT / 'docker/entrypoint.sh'), *arguments], env=environment, check=True)
            return (directory / 'trace').read_text().splitlines()

    def test_development_migrates_then_runs_django(self):
        self.assertEqual(self.trace('runserver', '0.0.0.0:8000'), [
            'python manage.py migrate --noinput', 'python manage.py runserver 0.0.0.0:8000'])

    def test_fullstack_migrates_collects_static_and_runs_gunicorn(self):
        self.assertEqual(self.trace('gunicorn', 'SmileManager.wsgi:application'), [
            'python manage.py migrate --noinput', 'python manage.py collectstatic --noinput',
            'gunicorn SmileManager.wsgi:application'])

    def test_management_commands_do_not_implicitly_migrate(self):
        self.assertEqual(self.trace('python', 'manage.py', 'check'), ['python manage.py check'])


if __name__ == '__main__':
    unittest.main()

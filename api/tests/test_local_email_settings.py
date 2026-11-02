import os
import subprocess
import sys

from django.test import SimpleTestCase


class LocalEmailSettingsTests(SimpleTestCase):
    def backend_for(self, delivery):
        env = os.environ.copy()
        env['DJANGO_SETTINGS_MODULE'] = 'SmileManager.settings_local'
        env['PYTHONDONTWRITEBYTECODE'] = '1'
        if delivery is None:
            env.pop('DEV_EMAIL_DELIVERY', None)
        else:
            env['DEV_EMAIL_DELIVERY'] = delivery
        return subprocess.run(
            [sys.executable, '-B', '-c', 'from django.conf import settings; print(settings.EMAIL_BACKEND)'],
            capture_output=True, text=True, env=env, timeout=30, check=False,
        )

    def test_default_delivery_is_local_file(self):
        result = self.backend_for(None)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), 'django.core.mail.backends.filebased.EmailBackend')

    def test_smtp_requires_explicit_opt_in(self):
        result = self.backend_for('smtp')
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), 'django.core.mail.backends.smtp.EmailBackend')

    def test_unknown_delivery_mode_fails_closed(self):
        self.assertNotEqual(self.backend_for('invalid').returncode, 0)

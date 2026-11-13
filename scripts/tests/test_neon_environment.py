"""Protect database selection and credential precedence without cloud access."""
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from SmileManager.environment import configure_postgres, database_url, load_environment


class NeonEnvironmentTests(unittest.TestCase):
    def test_deployment_env_wins_over_files_and_local_wins_over_dotenv(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / '.env.local').write_text('DATABASE_URL=local\nNEON_BRANCH=production\n')
            (root / '.env').write_text('DATABASE_URL=other\nNEON_BRANCH=other\n')
            with patch.dict(os.environ, {'DATABASE_URL': 'deployment'}, clear=True):
                load_environment(root)
                self.assertEqual(os.environ['DATABASE_URL'], 'deployment')
                self.assertEqual(os.environ['NEON_BRANCH'], 'production')

    def test_isolated_tests_do_not_load_cloud_secrets(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / '.env.local').write_text('DATABASE_URL=cloud\n')
            with patch.dict(os.environ, {'DJANGO_SETTINGS_MODULE': 'SmileManager.settings_test'}, clear=True):
                load_environment(root)
                self.assertNotIn('DATABASE_URL', os.environ)

    def test_migrations_use_direct_connection_and_runtime_uses_pool(self):
        with patch.dict(os.environ, {'DATABASE_URL': 'pooled', 'DATABASE_URL_UNPOOLED': 'direct'}, clear=True):
            with patch.object(sys, 'argv', ['manage.py', 'migrate']):
                self.assertEqual(database_url(), 'direct')
            with patch.object(sys, 'argv', ['manage.py', 'runserver']):
                self.assertEqual(database_url(), 'pooled')

    def test_pooling_disables_server_side_cursors(self):
        result = configure_postgres({'ENGINE': 'django.db.backends.postgresql', 'HOST': 'ep-test-pooler.us-east-2.aws.neon.tech'})
        self.assertTrue(result['DISABLE_SERVER_SIDE_CURSORS'])
        self.assertTrue(result['CONN_HEALTH_CHECKS'])

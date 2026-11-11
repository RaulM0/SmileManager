"""Prevent sensitive paths while allowing source assets."""
from django.test import SimpleTestCase
from scripts.check_sensitive_tracking import category


class SensitiveTrackingTests(SimpleTestCase):
    def test_blocks_data_and_credentials_in_nested_directories(self):
        for path in ('media/a.jpg', 'nested/uploads/identity.pdf', '.env', '.env.production',
                     'db.sqlite3', 'backup.SQL', 'nested/.aws/credentials', 'tls/server.key'):
            with self.subTest(path=path):
                self.assertIsNotNone(category(path))

    def test_allows_code_and_configuration_templates(self):
        for path in ('api/upload_policy.py', 'docs/security-audit.md', '.env.example',
                     'frontend/src/components/images/ProtectedImage.tsx', 'frontend/package-lock.json'):
            with self.subTest(path=path):
                self.assertIsNone(category(path))

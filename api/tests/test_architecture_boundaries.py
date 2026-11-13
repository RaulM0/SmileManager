"""Keep domain modules independent of the HTTP adapter and optional AI runtime."""
import ast
import subprocess
import sys

from django.conf import settings
from django.test import SimpleTestCase


class ArchitectureBoundaryTests(SimpleTestCase):
    def test_domain_modules_do_not_import_api_adapters(self):
        for app in ('Usuarios', 'Pacientes', 'Citas', 'DiagnosticosIA'):
            for path in (settings.BASE_DIR / app).rglob('*.py'):
                # Management commands are entry-point adapters, like HTTP views.
                if {'migrations', 'management'} & set(path.parts) or path.name.startswith('test'):
                    continue
                tree = ast.parse(path.read_text())
                for node in ast.walk(tree):
                    modules = ([node.module or ''] if isinstance(node, ast.ImportFrom) else
                               [alias.name for alias in node.names] if isinstance(node, ast.Import) else [])
                    for module in modules:
                        with self.subTest(path=str(path.relative_to(settings.BASE_DIR)), module=module):
                            self.assertNotEqual(module.split('.')[0], 'api')

    def test_importing_ai_services_does_not_load_runtime_or_read_model(self):
        code = """
import sys
from unittest.mock import patch
with patch('builtins.open', side_effect=AssertionError('Unexpected model access')):
    import DiagnosticosIA.services
assert 'ultralytics' not in sys.modules
assert 'torch' not in sys.modules
"""
        result = subprocess.run([sys.executable, '-c', code], cwd=settings.BASE_DIR,
                                capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_ai_runtime_and_artifact_are_external(self):
        self.assertFalse((settings.BASE_DIR / 'train_model').exists())
        source = (settings.BASE_DIR / 'DiagnosticosIA' / 'services.py').read_text()
        self.assertNotIn('ultralytics', source)
        self.assertNotIn('torch', source)

"""Keep domain modules independent of the HTTP adapter and optional AI runtime."""
import ast
from concurrent.futures import ThreadPoolExecutor
import subprocess
import sys
from types import SimpleNamespace
from unittest.mock import patch

from django.conf import settings
from django.test import SimpleTestCase

from DiagnosticosIA import services


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

    def test_concurrent_model_requests_initialize_only_once(self):
        model = object()
        runtime = SimpleNamespace(YOLO=lambda _: model)
        with patch.object(services, '_model', None), patch.object(services, 'model_version'), \
                patch.dict(sys.modules, {'ultralytics': runtime}), patch.object(runtime, 'YOLO', return_value=model) as load:
            with ThreadPoolExecutor(max_workers=4) as pool:
                results = list(pool.map(lambda _: services.get_model(), range(8)))
            self.assertTrue(all(result is model for result in results))
            load.assert_called_once()

    def test_failed_model_load_can_be_retried(self):
        model = object()
        runtime = SimpleNamespace(YOLO=lambda _: model)
        with patch.object(services, '_model', None), patch.object(services, 'model_version'), \
                patch.dict(sys.modules, {'ultralytics': runtime}), \
                patch.object(runtime, 'YOLO', side_effect=[RuntimeError('Unavailable model'), model]) as load:
            with self.assertRaises(RuntimeError):
                services.get_model()
            self.assertIs(services.get_model(), model)
            self.assertEqual(load.call_count, 2)

"""Real commits in disposable repositories; never mutate the project's index."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


class CodexHookTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix='smile-codex-hook-')
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.environment = {key: value for key, value in os.environ.items() if not key.startswith('GIT_')}
        for relative in ('scripts/build_project_map.py', 'scripts/update_obsidian_hook.py', 'scripts/codex_git.py', 'scripts/codex_obsidian_hook.py', '.githooks/pre-commit'):
            destination = self.root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / relative, destination)
        self.git('init', '-q')
        self.git('config', 'user.name', 'Synthetic Hook Test')
        self.git('config', 'user.email', 'synthetic@example.test')
        (self.root / 'api').mkdir()
        self.source = self.root / 'api/example.py'
        self.source.write_text('def staged_symbol():\n    pass\n')
        self.git('add', '.')

    def git(self, *args):
        return subprocess.check_output(['git', *args], cwd=self.root, env=self.environment).decode()

    def commit(self, *args):
        subprocess.run([sys.executable, str(self.root / 'scripts/codex_git.py'), 'commit', '-qm', 'Synthetic fixture', *args],
                       cwd=self.root, env=self.environment, check=True, capture_output=True)

    def note(self):
        return self.git('show', 'HEAD:docs/mapa/archivos/api_2Fexample.py.md')

    def test_commit_maps_index_and_preserves_unstaged_source(self):
        self.source.write_text('def unstaged_symbol():\n    pass\n')
        (self.root / 'api/private_draft.py').write_text('def not_committed():\n    pass\n')
        self.commit()
        self.assertIn('staged_symbol', self.note())
        self.assertNotIn('unstaged_symbol', self.note())
        self.assertIn('unstaged_symbol', self.source.read_text())
        self.assertNotIn('private_draft', self.git('ls-tree', '-r', '--name-only', 'HEAD'))
        self.assertEqual(self.git('config', '--get-regexp', '^user\\.').count('\n'), 2)
        result = subprocess.run(['git', 'config', '--get', 'core.hooksPath'], cwd=self.root, env=self.environment)
        self.assertEqual(result.returncode, 1)

    def test_commit_all_maps_auto_staged_changes(self):
        self.commit()
        self.source.write_text('def updated_symbol():\n    pass\n')
        self.commit('--all')
        self.assertIn('updated_symbol', self.note())

    def test_deletion_prunes_generated_note_and_preserves_manual_notes(self):
        self.commit()
        manual = self.root / 'docs/mapa/archivos/manual.md'
        manual.write_text('# Manual explanation\n')
        self.git('add', str(manual))
        self.git('rm', 'api/example.py')
        self.commit()
        files = self.git('ls-tree', '-r', '--name-only', 'HEAD')
        self.assertNotIn('api_2Fexample.py.md', files)
        self.assertIn('docs/mapa/archivos/manual.md', files)

    def test_unstaged_note_edit_is_preserved(self):
        self.commit()
        note = self.root / 'docs/mapa/archivos/api_2Fexample.py.md'
        note.write_text(note.read_text() + '\nPersonal draft\n')
        self.source.write_text('def next_symbol():\n    pass\n')
        self.git('add', 'api/example.py')
        self.commit()
        self.assertIn('next_symbol', self.note())
        self.assertNotIn('Personal draft', self.note())
        self.assertIn('Personal draft', note.read_text())

    def test_codex_event_rewrite_keeps_shell_command_and_ignores_other_tools(self):
        spec = importlib.util.spec_from_file_location('codex_hook_test', ROOT / 'scripts/codex_obsidian_hook.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        command = 'git add api/example.py && git commit -m "Synthetic message"'
        event = {'hook_event_name': 'PreToolUse', 'tool_input': {'command': command}}
        output = module.response(event)['hookSpecificOutput']
        self.assertTrue(output['updatedInput']['command'].endswith(command))
        self.assertEqual(module.response({'hook_event_name': 'PostToolUse'}), {})
        self.assertEqual(module.response({'hook_event_name': 'PreToolUse', 'tool_input': {'command': 'git status'}}), {})
        environment = self.environment
        subprocess.run(['sh', '-c', output['updatedInput']['command'].replace(str(ROOT), str(self.root))], cwd=self.root,
                       env=environment, check=True, capture_output=True)
        self.assertIn('staged_symbol', self.note())


if __name__ == '__main__':
    unittest.main()

"""Launch Codex with the repo hook, without writing protected .codex files."""
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def toml(value):
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, list):
        return '[' + ', '.join(toml(item) for item in value) + ']'
    if isinstance(value, dict):
        return '{' + ', '.join(json.dumps(key) + ' = ' + toml(item) for key, item in value.items()) + '}'
    if isinstance(value, bool):
        return str(value).lower()
    return str(value)


def arguments():
    configuration = json.loads((ROOT / 'codex/hooks.json').read_text())
    args = []
    for event, groups in configuration['hooks'].items():
        args += ['-c', 'hooks.' + event + '=' + toml(groups)]
    return args


if __name__ == '__main__':
    executable = shutil.which('codex')
    if not executable:
        raise SystemExit('Codex CLI is required.')
    sys.exit(subprocess.run([executable, *arguments(), *sys.argv[1:]], cwd=ROOT).returncode)

"""Codex-scoped Git adapter: enable the map hook only for this repo's commits."""
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
VALUE_OPTIONS = {'-C', '-c', '--git-dir', '--work-tree', '--namespace', '--config-env', '--super-prefix'}


def subcommand(args):
    index = 0
    while index < len(args):
        value = args[index]
        if value in VALUE_OPTIONS:
            index += 2
        elif value.startswith('-'):
            index += 1
        else:
            return index
    return None


def main(args):
    git = shutil.which('git')
    if git is None:
        raise SystemExit('Git is required.')
    index = subcommand(args)
    if index is not None and args[index] == 'commit':
        result = subprocess.run([git, *args[:index], 'rev-parse', '--show-toplevel'], capture_output=True, text=True)
        if result.returncode == 0 and Path(result.stdout.strip()).resolve() == ROOT:
            args = [*args[:index], '-c', 'core.hooksPath=' + str(ROOT / '.githooks'), *args[index:]]
    return subprocess.run([git, *args]).returncode


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

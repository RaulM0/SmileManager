"""Stage an Obsidian map of the index, preserving unstaged source and note edits."""
from pathlib import Path
import subprocess
import sys

import build_project_map as project_map

ROOT = Path(__file__).resolve().parents[1]


def git(*args, data=None):
    return subprocess.check_output(['git', *args], cwd=ROOT, input=data)


def indexed(path):
    result = subprocess.run(['git', 'show', ':' + path], cwd=ROOT, capture_output=True)
    return result.stdout if result.returncode == 0 else None


def main():
    project_map.ROOT = ROOT
    output = {'docs/mapa/' + name: text.encode('utf-8') for name, text in project_map.render(staged=True).items()}
    updates, files, removals = [], [], []
    preserved = 0
    for path, content in output.items():
        old = indexed(path)
        file = ROOT / path
        if old != content:
            oid = git('hash-object', '-w', '--stdin', data=content).strip()
            updates.append(b'100644 ' + oid + b'\t' + path.encode() + b'\0')
        current = file.read_bytes() if file.is_file() and not file.is_symlink() else None
        if not file.exists() or (not file.is_symlink() and current == old):
            files.append((file, content))
        elif current != content:
            preserved += 1
    # Only prune indexed notes that identify themselves as generated source notes.
    for raw in git('ls-files', '-z', '--', 'docs/mapa/archivos/').split(b'\0'):
        if not raw:
            continue
        path = raw.decode()
        if path in output:
            continue
        old = indexed(path)
        if not old or not old.startswith(b'---\ngenerated: true\nsource: '):
            continue
        zero = b'0' * len(git('hash-object', '--stdin', data=b'').strip())
        updates.append(b'0 ' + zero + b'\t' + raw + b'\0')
        file = ROOT / path
        if file.is_file() and not file.is_symlink() and file.read_bytes() == old:
            removals.append(file)
        elif file.exists():
            preserved += 1
    # A single index transaction; honors GIT_INDEX_FILE used by partial commits.
    if updates:
        subprocess.run(['git', 'update-index', '-z', '--index-info'], cwd=ROOT, input=b''.join(updates), check=True)
    for file, content in files:
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(content)
    for file in removals:
        file.unlink()
    print(f'Obsidian: mapa del commit actualizado ({len(output)} notas generadas; {preserved} cambios locales conservados).')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, RuntimeError, SyntaxError, subprocess.CalledProcessError) as error:
        print(f'Obsidian: no se pudo actualizar el mapa; commit cancelado. {error}', file=sys.stderr)
        sys.exit(1)

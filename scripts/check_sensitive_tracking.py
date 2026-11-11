"""Reject sensitive storage paths in the index without opening or printing data."""
from collections import Counter
from pathlib import PurePosixPath
import subprocess
import sys


def category(path):
    parts = PurePosixPath(path.casefold()).parts
    name = parts[-1]
    if any(part in {'media', 'uploads', '.aws', '.ssh', '.local-mail', '.e2e-browser-mail'} for part in parts):
        return 'clinical-storage-or-local-credentials'
    if name == '.env' or (name.startswith('.env.') and name != '.env.example') or name.endswith('.env'):
        return 'environment-secrets'
    if name.endswith(('.sqlite3', '.sqlite3-journal', '.sqlite3-wal', '.sqlite3-shm', '.db', '.dump', '.sql', '.pem', '.key')):
        return 'database-or-private-key'
    return None


def main():
    result = subprocess.run(['git', 'ls-files', '--cached', '-z'], capture_output=True, check=True)
    counts = Counter()
    for raw in result.stdout.split(b'\0'):
        if raw:
            label = category(raw.decode('utf-8', errors='surrogateescape'))
            if label:
                counts[label] += 1
    if counts:
        print('FAIL: archivos sensibles rastreados; no se muestran nombres ni contenido.')
        for label, count in sorted(counts.items()):
            print(f'{label}: {count}')
        return 1
    print('PASS: sin archivos rastreados en categorías sensibles bloqueadas.')
    return 0


if __name__ == '__main__':
    sys.exit(main())

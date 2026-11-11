"""Encrypted local backup and isolated restore drill. Requires Docker Compose."""
import argparse
import fcntl
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import secrets
import subprocess
import tarfile
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
CONFIG = ROOT / '.local-ops.env'
if not CONFIG.exists():
    raise SystemExit('Run python3 scripts/setup_dev_security.py first.')
for line in CONFIG.read_text().splitlines():
    if line and not line.startswith('#'):
        key, value = line.split('=', 1)
        os.environ[key] = value
COMPOSE = ['docker', 'compose', '--env-file', str(CONFIG)]


def run(args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)


def helper(mode, source, target):
    run(COMPOSE + ['run', '--rm', '--no-deps', '-T', '-e', 'BACKUP_KEY', '--entrypoint', 'python',
                   'backend', 'scripts/backup_crypto.py', mode], stdin=source, stdout=target)


def report(command):
    output = subprocess.check_output(command, text=True)
    return json.loads(output.strip().splitlines()[-1])


def create(destination):
    destination = destination.resolve()
    destination.mkdir(parents=True, exist_ok=True, mode=0o700)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    target = destination / (stamp + '-' + secrets.token_hex(3) + '.smilebackup')
    running = subprocess.check_output(COMPOSE + ['ps', '--status', 'running', '--services'], text=True).splitlines()
    writers = [service for service in ('security-worker', 'backend') if service in running]
    if 'backend' not in running:
        raise SystemExit('Start the local stack before backing it up.')
    started = time.monotonic()
    try:
        if writers:
            run(COMPOSE + ['stop'] + writers)
        with tempfile.TemporaryDirectory(prefix='smile-backup-') as temp:
            directory = Path(temp)
            state = report(COMPOSE + ['run', '--rm', '--no-deps', '-T', '--entrypoint', 'python', 'backend', 'manage.py', 'check_restored_state'])
            with (directory / 'database.dump').open('wb') as file:
                run(COMPOSE + ['exec', '-T', 'db', 'pg_dump', '-U', 'smilemanager', '-d', 'smilemanager', '-Fc'], stdout=file)
            with (directory / 'media.tar').open('wb') as file:
                run(COMPOSE + ['run', '--rm', '--no-deps', '-T', '--entrypoint', 'python', 'backend', 'scripts/backup_files.py', 'pack'], stdout=file)
            with (directory / 'audit.sqlite3').open('wb') as file:
                run(COMPOSE + ['exec', '-T', 'audit-collector', 'python', 'docker/audit_collector.py', '--snapshot'], stdout=file)
            manifest = {'created_at': datetime.now(timezone.utc).isoformat(), 'state': state, 'format': 1, 'source_image': subprocess.check_output(COMPOSE + ['images', '-q', 'backend'], text=True).strip().splitlines()[0]}
            (directory / 'manifest.json').write_text(json.dumps(manifest))
            bundle = directory / 'bundle.tar'
            with tarfile.open(bundle, 'w') as archive:
                for name in ('database.dump', 'media.tar', 'audit.sqlite3', 'manifest.json'):
                    archive.add(directory / name, arcname=name)
            with bundle.open('rb') as source, target.with_suffix('.incomplete').open('xb') as output:
                os.chmod(output.name, 0o600)
                helper('encrypt', source, output)
            target.with_suffix('.incomplete').rename(target)
    finally:
        if writers:
            run(COMPOSE + ['start'] + writers)
    run(COMPOSE + ['exec', '-T', 'backend', 'python', 'manage.py', 'record_backup_success'])
    print(json.dumps({'backup': str(target), 'seconds': round(time.monotonic() - started, 2)}))


def restore(backup):
    started = time.monotonic()
    token = 'smile-restore-' + secrets.token_hex(5)
    db, network, media = token + '-db', token + '-network', token + '-media'
    image = os.environ.get('SMILE_RESTORE_IMAGE', 'smilemanager-backend:latest')
    environment = os.environ.copy()
    container = subprocess.check_output(COMPOSE + ['ps', '-q', 'backend'], text=True).strip()
    runtime = json.loads(subprocess.check_output(['docker', 'inspect', container], text=True))[0]['Config']['Env'] if container else []
    custody = {'AUDIT_SIGNING_KEYS', 'FILE_SCAN_KEYS', 'MFA_ENCRYPTION_KEYS', 'DOCUMENT_SEAL_KEYS'}
    for item in runtime:
        key, value = item.split('=', 1)
        if key in custody:
            environment[key] = value
    environment['POSTGRES_PASSWORD'] = secrets.token_urlsafe(32)
    environment['DATABASE_URL'] = 'postgresql://smilemanager:' + environment['POSTGRES_PASSWORD'] + '@' + db + ':5432/smilemanager'
    environment['DJANGO_SETTINGS_MODULE'] = 'SmileManager.settings_local'
    def app(command, **kwargs):
        args = ['docker', 'run', '--rm', '-i', '--network', network, '--user', '1000:1000', '-v', str(ROOT) + ':/app:ro', '-v', '/dev/null:/app/.local-ops.env:ro',
                '-v', media + ':/app/media', '-w', '/app']
        for key in ('DATABASE_URL', 'DJANGO_SETTINGS_MODULE', 'AUDIT_SIGNING_KEYS', 'FILE_SCAN_KEYS', 'MFA_ENCRYPTION_KEYS', 'DOCUMENT_SEAL_KEYS'):
            if key in environment:
                args += ['-e', key]
        return args + ['--entrypoint', 'python', image] + command
    try:
        with tempfile.TemporaryDirectory(prefix='smile-restore-') as temp:
            directory = Path(temp)
            with backup.open('rb') as source, (directory / 'bundle.tar').open('wb') as output:
                helper('decrypt', source, output)
            with tarfile.open(directory / 'bundle.tar', 'r') as archive:
                members = archive.getmembers()
                names = {'database.dump', 'media.tar', 'audit.sqlite3', 'manifest.json'}
                if len(members) != 4 or {m.name for m in members} != names or any(not m.isfile() for m in members):
                    raise SystemExit('Invalid backup manifest.')
                archive.extractall(directory, filter='data')
            manifest = json.loads((directory / 'manifest.json').read_text())
            run(['docker', 'network', 'create', '--internal', network], stdout=subprocess.DEVNULL)
            run(['docker', 'volume', 'create', media], stdout=subprocess.DEVNULL)
            run(['docker', 'run', '--rm', '--user', '0:0', '-v', media + ':/media', '--entrypoint', 'sh', image, '-c', 'chown 1000:1000 /media'])
            run(['docker', 'run', '-d', '--name', db, '--network', network, '-e', 'POSTGRES_PASSWORD',
                 '-e', 'POSTGRES_USER=smilemanager', '-e', 'POSTGRES_DB=smilemanager', 'postgres:16-alpine'], env=environment, stdout=subprocess.DEVNULL)
            for _ in range(60):
                if subprocess.run(['docker', 'exec', db, 'pg_isready', '-U', 'smilemanager'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0:
                    break
                time.sleep(1)
            else:
                raise SystemExit('Restore database did not become ready.')
            with (directory / 'database.dump').open('rb') as source:
                run(['docker', 'exec', '-i', db, 'pg_restore', '-U', 'smilemanager', '-d', 'smilemanager', '--no-owner', '--no-acl', '--exit-on-error'], stdin=source)
            with (directory / 'media.tar').open('rb') as source:
                run(app(['scripts/backup_files.py', 'unpack']), env=environment, stdin=source)
            state = report_with_env(app(['manage.py', 'check_restored_state']), environment)
            if state != manifest['state']:
                raise SystemExit('Restored state differs from the backup manifest.')
            environment['AUDIT_JOURNAL_PATH'] = '/restore/audit.sqlite3'
            run(['docker', 'run', '--rm', '--network', 'none', '-e', 'AUDIT_JOURNAL_PATH', '-e', 'AUDIT_SIGNING_KEYS',
                 '-v', str(ROOT) + ':/app:ro', '-v', '/dev/null:/app/.local-ops.env:ro', '-v', str(directory) + ':/restore', '--entrypoint', 'python', image,
                 '/app/docker/audit_collector.py', '--verify'], env=environment)
            result = {'restore': 'verified', 'backup_created_at': manifest['created_at'], 'seconds': round(time.monotonic() - started, 2), 'isolated': True}
            destination = backup.with_suffix('.restore.json')
            destination.write_text(json.dumps(result, indent=2))
            os.chmod(destination, 0o600)
            print(json.dumps(result))
    finally:
        subprocess.run(['docker', 'rm', '-fv', db], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(['docker', 'volume', 'rm', media], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(['docker', 'network', 'rm', network], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def report_with_env(command, environment):
    output = subprocess.check_output(command, text=True, env=environment)
    return json.loads(output.strip().splitlines()[-1])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['create', 'restore'])
    parser.add_argument('path', type=Path, nargs='?', default=ROOT / '.local-backups')
    args = parser.parse_args()
    lock = open('/tmp/smilemanager-dev-backup-' + str(os.getuid()) + '.lock', 'a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    create(args.path) if args.action == 'create' else restore(args.path.resolve())

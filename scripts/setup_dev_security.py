"""Create local operational secrets without changing existing clinical/MFA keys."""
import os
from pathlib import Path
import secrets

path = Path('.local-ops.env')
if path.exists():
    raise SystemExit('Existing configuration retained.')
values = {name: secrets.token_urlsafe(48) for name in ('AUDIT_SIGNING_KEYS', 'AUDIT_INGEST_TOKEN', 'FILE_SCAN_KEYS')}
values['BACKUP_KEY'] = secrets.token_hex(32)
fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
with os.fdopen(fd, 'w') as file:
    file.write(''.join(f'{name}={value}\n' for name, value in values.items()))
print('Created private development configuration: .local-ops.env')

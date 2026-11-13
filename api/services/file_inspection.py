"""Private PDF quarantine. Unavailable scanners never release documents."""
import hashlib
import hmac
import socket
import struct
import subprocess
import sys
import uuid
from datetime import datetime, timedelta, timezone as datetime_timezone
from pathlib import Path

from django.conf import settings
from django.core.files.storage import default_storage
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import APIException
from Usuarios.models import FileInspection


class QuarantinedFile(APIException):
    status_code = 423
    default_detail = 'Documento en cuarentena; pendiente de revisión de seguridad.'
    default_code = 'file_quarantined'


def queue(name, digest):
    row, _ = FileInspection.objects.get_or_create(storage_name=name, defaults={'expected_sha256': digest})
    return row


def signature(row, key):
    value = f'{row.storage_name}\n{row.expected_sha256}\n{row.status}\n{row.checked_at.isoformat() if row.checked_at else ""}'
    return hmac.new(key.encode(), value.encode(), hashlib.sha256).hexdigest()


def require_clean(name, digest):
    if not name.lower().endswith('.pdf'):
        return
    row = queue(name, digest)
    if row.expected_sha256 != digest or row.status != 'CLEAN' or not row.checked_at or not any(
            hmac.compare_digest(row.seal, signature(row, key)) for key in settings.FILE_SCAN_KEYS):
        raise QuarantinedFile()


def scan_status(name):
    if not name.lower().endswith('.pdf'):
        return 'NOT_REQUIRED'
    row = FileInspection.objects.filter(storage_name=name).first()
    if not row:
        return 'PENDING'
    if row.status == 'CLEAN' and not any(hmac.compare_digest(row.seal, signature(row, key)) for key in settings.FILE_SCAN_KEYS):
        return 'ERROR'
    return row.status


def clamav(data):
    if not settings.CLAMAV_HOST:
        raise OSError('scanner_unconfigured')
    # Refuse stale signatures even when the daemon would otherwise return OK.
    with socket.create_connection((settings.CLAMAV_HOST, settings.CLAMAV_PORT), timeout=10) as version_connection:
        version_connection.settimeout(10)
        version_connection.sendall(b'zVERSION\0')
        raw_version = version_connection.recv(1024).rstrip(b'\0\n')
    try:
        version = raw_version.decode('ascii')
    except UnicodeError:
        raise OSError('scanner_invalid_version') from None
    try:
        signature_date = datetime.strptime(version.split('/', 2)[2], '%a %b %d %H:%M:%S %Y').replace(tzinfo=datetime_timezone.utc)
        age = timezone.now() - signature_date
        if age < timedelta(days=-1) or age > timedelta(days=3):
            raise ValueError('stale')
    except (ValueError, IndexError):
        raise OSError('scanner_signatures_stale') from None
    with socket.create_connection((settings.CLAMAV_HOST, settings.CLAMAV_PORT), timeout=10) as connection:
        connection.settimeout(20)
        connection.sendall(b'zINSTREAM\0')
        for start in range(0, len(data), 65536):
            chunk = data[start:start + 65536]
            connection.sendall(struct.pack('!I', len(chunk)) + chunk)
        connection.sendall(struct.pack('!I', 0))
        response = bytearray()
        while len(response) < 4096:
            part = connection.recv(4096 - len(response))
            if not part:
                break
            response.extend(part)
            if b'\0' in response:
                break
    answer = bytes(response).rstrip(b'\0\n')
    if answer == b'stream: OK':
        return True
    if answer.startswith(b'stream: ') and answer.endswith(b' FOUND'):
        return False
    raise OSError('scanner_error')


def process_one():
    now = timezone.now()
    with transaction.atomic():
        row = FileInspection.objects.select_for_update(skip_locked=True).filter(
            Q(status='PENDING') | Q(status='ERROR', checked_at__lt=now - timedelta(minutes=5)) |
            Q(status='SCANNING', checked_at__lt=now - timedelta(minutes=10))).order_by('pk').first()
        if row is None:
            return False
        row.status, row.checked_at, row.claim_id = 'SCANNING', now, uuid.uuid4()
        row.save(update_fields=['status', 'checked_at', 'claim_id'])
    status, reason = 'ERROR', 'scanner_unavailable'
    try:
        with default_storage.open(row.storage_name, 'rb') as file:
            data = file.read(settings.CLINICAL_UPLOAD_MAX_BYTES + 1)
        if len(data) > settings.CLINICAL_UPLOAD_MAX_BYTES or hashlib.sha256(data).hexdigest() != row.expected_sha256:
            status, reason = 'REJECTED', 'content_mismatch'
        elif not clamav(data):
            status, reason = 'REJECTED', 'malware'
        else:
            result = subprocess.run([sys.executable, str(Path(settings.BASE_DIR) / 'scripts/pdf_inspect.py')],
                                    input=data, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10, check=False)
            status, reason = ('CLEAN', '') if result.returncode == 0 else ('REJECTED', 'pdf_structure')
    except (OSError, subprocess.TimeoutExpired):
        pass
    row.status, row.reason, row.checked_at = status, reason, timezone.now()
    row.seal = signature(row, settings.FILE_SCAN_KEYS[0])
    # A stale worker cannot overwrite a later worker's result.
    FileInspection.objects.filter(pk=row.pk, claim_id=row.claim_id, status='SCANNING').update(
        status=row.status, reason=row.reason, checked_at=row.checked_at, seal=row.seal)
    return True

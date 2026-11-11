import hashlib
import io
import subprocess
import sys
import uuid
from pathlib import Path
from unittest.mock import patch
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.test import TestCase
from pypdf import PdfWriter
from Usuarios.models import AuditEvent, FileInspection
from Usuarios.audit_integrity import verify
from api.services.file_inspection import QuarantinedFile, process_one, queue, require_clean


def pdf(javascript=False):
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    if javascript:
        writer.add_js('app.alert("synthetic")')
    target = io.BytesIO()
    writer.write(target)
    return target.getvalue()


class StageThreeTests(TestCase):
    def test_audit_seal_and_append_only(self):
        event = AuditEvent.objects.create(action='TEST', request_id=uuid.uuid4())
        self.assertTrue(verify(event))
        event.action = 'ALTERED'
        self.assertFalse(verify(event))
        with self.assertRaises(ValidationError):
            event.save()
        with self.assertRaises(ValidationError):
            AuditEvent.objects.filter(pk=event.pk).update(action='ALTERED')
        with self.assertRaises(ValidationError):
            event.delete()

    def test_pdf_structure_rejects_active_encrypted_and_malformed(self):
        script = str(Path(settings.BASE_DIR) / 'scripts/pdf_inspect.py')
        writer = PdfWriter()
        writer.add_blank_page(width=10, height=10)
        writer.encrypt('synthetic')
        encrypted = io.BytesIO()
        writer.write(encrypted)
        for data, code in [(pdf(), 0), (pdf(True), 2), (encrypted.getvalue(), 2), (b'%PDF-1.4\ninvalid\n%%EOF', 2)]:
            result = subprocess.run([sys.executable, script], input=data, capture_output=True, timeout=15)
            self.assertEqual(result.returncode, code)

    def test_quarantine_requires_real_processing_and_sealed_result(self):
        data = pdf()
        name = default_storage.save('synthetic/' + str(uuid.uuid4()) + '.pdf', ContentFile(data))
        self.addCleanup(default_storage.delete, name)
        digest = hashlib.sha256(data).hexdigest()
        row = queue(name, digest)
        with self.assertRaises(QuarantinedFile):
            require_clean(name, digest)
        with patch('api.services.file_inspection.clamav', return_value=True):
            self.assertTrue(process_one())
        require_clean(name, digest)
        FileInspection.objects.filter(pk=row.pk).update(seal='0' * 64)
        with self.assertRaises(QuarantinedFile):
            require_clean(name, digest)

    def test_scanner_outage_does_not_release(self):
        data = pdf()
        name = default_storage.save('synthetic/' + str(uuid.uuid4()) + '.pdf', ContentFile(data))
        self.addCleanup(default_storage.delete, name)
        digest = hashlib.sha256(data).hexdigest()
        queue(name, digest)
        with patch('api.services.file_inspection.clamav', side_effect=OSError):
            process_one()
        self.assertEqual(FileInspection.objects.get(storage_name=name).status, 'ERROR')
        with self.assertRaises(QuarantinedFile):
            require_clean(name, digest)

    def test_stale_antivirus_signatures_fail_closed(self):
        from api.services.file_inspection import clamav
        from django.test import override_settings
        with override_settings(CLAMAV_HOST='scanner.internal'), patch('api.services.file_inspection.socket.create_connection') as connect:
            connect.return_value.__enter__.return_value.recv.return_value = b'ClamAV 1.5.4/1/Sat Jan  1 00:00:00 2000\0'
            with self.assertRaises(OSError):
                clamav(pdf())

    def test_malware_result_blocks_but_preserves_original(self):
        data = pdf()
        name = default_storage.save('synthetic/' + str(uuid.uuid4()) + '.pdf', ContentFile(data))
        self.addCleanup(default_storage.delete, name)
        digest = hashlib.sha256(data).hexdigest()
        queue(name, digest)
        with patch('api.services.file_inspection.clamav', return_value=False):
            process_one()
        row = FileInspection.objects.get(storage_name=name)
        self.assertEqual((row.status, row.reason), ('REJECTED', 'malware'))
        self.assertTrue(default_storage.exists(name))
        with self.assertRaises(QuarantinedFile):
            require_clean(name, digest)

    def test_changed_file_rejected_before_scanner(self):
        name = default_storage.save('synthetic/' + str(uuid.uuid4()) + '.pdf', ContentFile(pdf()))
        self.addCleanup(default_storage.delete, name)
        queue(name, '0' * 64)
        with patch('api.services.file_inspection.clamav') as scanner:
            process_one()
        scanner.assert_not_called()
        self.assertEqual(FileInspection.objects.get(storage_name=name).reason, 'content_mismatch')


class AuditJournalTests(TestCase):
    def test_independent_journal_chain_and_idempotency_constraints(self):
        import importlib.util
        import json
        import os
        import sqlite3
        import tempfile
        spec = importlib.util.spec_from_file_location('audit_collector_test', Path(settings.BASE_DIR) / 'docker/audit_collector.py')
        collector = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(collector)
        event = AuditEvent.objects.create(action='JOURNAL_TEST', request_id=uuid.uuid4())
        from Usuarios.audit_integrity import payload
        document = {'payload': payload(event), 'content_sha256': event.content_sha256, 'integrity_seal': event.integrity_seal}
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {'AUDIT_SIGNING_KEYS': ','.join(settings.AUDIT_SIGNING_KEYS)}):
            collector.PATH = directory + '/journal.sqlite3'
            collector.validate(document)
            with collector.connect() as db:
                encoded = collector.canonical(document)
                previous = '0' * 64
                digest = hashlib.sha256((previous + encoded).encode()).hexdigest()
                db.execute('INSERT INTO entries(event_id,document,previous,digest) VALUES(?,?,?,?)', (str(event.event_id), encoded, previous, digest))
                self.assertEqual(collector.verify(db)['events'], 1)
                with self.assertRaises(sqlite3.IntegrityError):
                    db.execute('DELETE FROM entries')
                db.execute('DROP TRIGGER deny_UPDATE')
                db.execute("UPDATE entries SET digest='altered'")
                with self.assertRaises(ValueError):
                    collector.verify(db)
            document['payload']['action'] = 'ALTERED'
            with self.assertRaises(ValueError):
                collector.validate(document)

    def test_postgres_raw_sql_cannot_update_or_delete_audit(self):
        from django.db import connection, transaction, DatabaseError
        if connection.vendor != 'postgresql':
            self.skipTest('PostgreSQL trigger integration')
        event = AuditEvent.objects.create(action='GUARD_TEST', request_id=uuid.uuid4())
        for sql in ['UPDATE "Usuarios_auditevent" SET action=%s WHERE id=%s', 'DELETE FROM "Usuarios_auditevent" WHERE action=%s AND id=%s']:
            with self.assertRaises(DatabaseError), transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute(sql, ['GUARD_TEST', event.pk])

    def test_missing_worker_and_backup_are_operational_alerts(self):
        from django.core.management import call_command
        from django.core.management.base import CommandError
        with self.assertRaises(CommandError):
            call_command('check_security_operations', stdout=io.StringIO())


class AntivirusIntegrationTests(TestCase):
    def test_real_clamav_accepts_pdf_and_rejects_eicar(self):
        import os
        from django.test import override_settings
        from api.services.file_inspection import clamav
        host = os.environ.get('CLAMAV_TEST_HOST')
        if not host:
            self.skipTest('Set CLAMAV_TEST_HOST for real antivirus integration.')
        # EICAR is a harmless standardized antivirus test string.
        eicar = b'X5O!P%@AP[4\\PZX54(P^)7CC)7}$' + b'EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*'
        with override_settings(CLAMAV_HOST=host):
            self.assertTrue(clamav(pdf()))
            self.assertFalse(clamav(eicar))


class BackupCodecTests(TestCase):
    def test_encryption_roundtrip_and_tamper_emits_no_plaintext(self):
        import os
        import secrets
        script = str(Path(settings.BASE_DIR) / 'scripts/backup_crypto.py')
        environment = {**os.environ, 'BACKUP_KEY': secrets.token_hex(32)}
        original = b'synthetic restore fixture' * 10000
        encrypted = subprocess.run([sys.executable, script, 'encrypt'], input=original, capture_output=True, env=environment, check=True).stdout
        self.assertNotIn(b'synthetic restore fixture', encrypted)
        result = subprocess.run([sys.executable, script, 'decrypt'], input=encrypted, capture_output=True, env=environment, check=True)
        self.assertEqual(result.stdout, original)
        corrupted = bytearray(encrypted)
        corrupted[len(corrupted) // 2] ^= 1
        result = subprocess.run([sys.executable, script, 'decrypt'], input=corrupted, capture_output=True, env=environment)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b'')


class CollectorHTTPTests(TestCase):
    def test_authenticated_idempotent_delivery_and_tamper_rejection(self):
        import json
        import os
        import secrets
        import socket
        import tempfile
        import threading
        import urllib.error
        import urllib.request
        import importlib.util
        spec = importlib.util.spec_from_file_location('collector_http_test', Path(settings.BASE_DIR) / 'docker/audit_collector.py')
        collector = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(collector)
        from Usuarios.audit_integrity import payload
        event = AuditEvent.objects.create(action='HTTP_TEST', request_id=uuid.uuid4())
        document = {'payload': payload(event), 'content_sha256': event.content_sha256, 'integrity_seal': event.integrity_seal}
        token = secrets.token_urlsafe(32)
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {'AUDIT_SIGNING_KEYS': ','.join(settings.AUDIT_SIGNING_KEYS), 'AUDIT_INGEST_TOKEN': token}):
            collector.PATH = directory + '/journal.sqlite3'
            server = collector.ThreadingHTTPServer(('127.0.0.1', 0), collector.Handler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                url = f'http://127.0.0.1:{server.server_port}/events'
                def send(value, credential=token):
                    request = urllib.request.Request(url, data=json.dumps(value).encode(), headers={'Authorization': 'Bearer ' + credential})
                    with urllib.request.urlopen(request, timeout=5) as response:
                        return json.load(response)
                receipt = send(document)
                self.assertEqual(send(document), receipt)
                with collector.connect() as db:
                    self.assertEqual(collector.verify(db)['events'], 1)
                with self.assertRaises(urllib.error.HTTPError) as error:
                    send(document, 'invalid')
                self.assertEqual(error.exception.code, 403)
                document['payload']['action'] = 'TAMPERED'
                with self.assertRaises(urllib.error.HTTPError) as error:
                    send(document)
                self.assertEqual(error.exception.code, 400)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)

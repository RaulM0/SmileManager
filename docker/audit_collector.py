"""Local append-only audit journal. No retrieval, update or delete API."""
import hashlib
import hmac
import json
import os
import sqlite3
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

FIELDS = {'event_id', 'timestamp', 'clinic_id', 'actor_id', 'action', 'resource_type', 'resource_id', 'request_id', 'outcome'}
PATH = os.environ.get('AUDIT_JOURNAL_PATH', '/journal/audit.sqlite3')


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def connect():
    db = sqlite3.connect(PATH, timeout=20)
    db.execute('PRAGMA synchronous=FULL')
    db.execute('CREATE TABLE IF NOT EXISTS entries (sequence INTEGER PRIMARY KEY, event_id TEXT UNIQUE NOT NULL, document TEXT NOT NULL, previous TEXT NOT NULL, digest TEXT NOT NULL)')
    for operation in ('UPDATE', 'DELETE'):
        db.execute(f"CREATE TRIGGER IF NOT EXISTS deny_{operation} BEFORE {operation} ON entries BEGIN SELECT RAISE(ABORT, 'append_only'); END")
    db.commit()
    return db


def validate(document):
    if set(document) != {'payload', 'content_sha256', 'integrity_seal'} or set(document['payload']) != FIELDS:
        raise ValueError('schema')
    if not all(isinstance(value, str) and len(value) <= 128 for value in document['payload'].values()):
        raise ValueError('values')
    digest = hashlib.sha256(canonical(document['payload']).encode()).hexdigest()
    keys = [key for key in os.environ.get('AUDIT_SIGNING_KEYS', '').split(',') if key]
    if digest != document['content_sha256'] or not any(hmac.compare_digest(
            hmac.new(key.encode(), digest.encode(), hashlib.sha256).hexdigest(), document['integrity_seal']) for key in keys):
        raise ValueError('signature')


def verify(db):
    previous, count = '0' * 64, 0
    for sequence, document, link, digest in db.execute('SELECT sequence,document,previous,digest FROM entries ORDER BY sequence'):
        validate(json.loads(document))
        expected = hashlib.sha256((previous + document).encode()).hexdigest()
        if sequence != count + 1 or link != previous or digest != expected:
            raise ValueError('chain')
        previous, count = digest, count + 1
    return {'events': count, 'head': previous}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def reply(self, status, value):
        body = canonical(value).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path != '/health':
            return self.reply(404, {})
        with connect() as db:
            db.execute('SELECT 1')
        self.reply(200, {'status': 'ok'})

    def do_POST(self):
        self.connection.settimeout(10)
        token = os.environ.get('AUDIT_INGEST_TOKEN', '')
        if not token or not hmac.compare_digest(self.headers.get('Authorization', ''), 'Bearer ' + token):
            return self.reply(403, {})
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if self.path != '/events' or length < 1 or length > 8192:
                return self.reply(400, {})
            document = json.loads(self.rfile.read(length))
            validate(document)
            encoded = canonical(document)
            with connect() as db:
                db.execute('BEGIN IMMEDIATE')
                existing = db.execute('SELECT document,digest FROM entries WHERE event_id=?', (document['payload']['event_id'],)).fetchone()
                if existing:
                    if existing[0] != encoded:
                        return self.reply(409, {})
                    receipt = existing[1]
                else:
                    last = db.execute('SELECT digest FROM entries ORDER BY sequence DESC LIMIT 1').fetchone()
                    previous = last[0] if last else '0' * 64
                    receipt = hashlib.sha256((previous + encoded).encode()).hexdigest()
                    db.execute('INSERT INTO entries(event_id,document,previous,digest) VALUES(?,?,?,?)',
                               (document['payload']['event_id'], encoded, previous, receipt))
            self.reply(201, {'receipt': receipt})
        except (ValueError, TypeError, KeyError, OSError, sqlite3.Error):
            self.reply(400, {})


if __name__ == '__main__':
    if '--verify' in sys.argv:
        with connect() as db:
            print(canonical(verify(db)))
    elif '--snapshot' in sys.argv:
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            name = directory + '/snapshot.sqlite3'
            with connect() as source, sqlite3.connect(name) as destination:
                verify(source)
                source.backup(destination)
            with open(name, 'rb') as file:
                while chunk := file.read(65536):
                    sys.stdout.buffer.write(chunk)
    else:
        if len(os.environ.get('AUDIT_INGEST_TOKEN', '')) < 32 or not os.environ.get('AUDIT_SIGNING_KEYS'):
            sys.exit('Independent audit configuration is required.')
        ThreadingHTTPServer(('0.0.0.0', 8080), Handler).serve_forever()

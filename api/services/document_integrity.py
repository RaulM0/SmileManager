"""Application seals detect changes; these are not advanced electronic signatures."""
import hashlib
import hmac
import json
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder


def digest(payload):
    canonical = json.dumps(payload, cls=DjangoJSONEncoder, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    return hashlib.sha256(canonical.encode()).hexdigest()


def seal(payload):
    value = digest(payload)
    return value, hmac.new(settings.DOCUMENT_SEAL_KEYS[0].encode(), value.encode(), hashlib.sha256).hexdigest()


def verify(payload, expected_digest, expected_seal):
    actual = digest(payload)
    return hmac.compare_digest(actual, expected_digest) and any(
        hmac.compare_digest(hmac.new(key.encode(), actual.encode(), hashlib.sha256).hexdigest(), expected_seal)
        for key in settings.DOCUMENT_SEAL_KEYS
    )


def file_digest(file):
    value = hashlib.sha256()
    file.seek(0)
    for chunk in file.chunks() if hasattr(file, 'chunks') else iter(lambda: file.read(65536), b''):
        value.update(chunk)
    file.seek(0)
    return value.hexdigest()

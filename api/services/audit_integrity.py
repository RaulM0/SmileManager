"""Per-event seals; historical unsealed events remain explicitly unverifiable."""
import hashlib
import hmac
import json
from django.conf import settings

FIELDS = ('event_id', 'timestamp', 'clinic_id', 'actor_id', 'action', 'resource_type', 'resource_id', 'request_id', 'outcome')


def payload(event):
    return {field: str(getattr(event, field)) for field in FIELDS}


def sign(value):
    digest = hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()
    return digest, hmac.new(settings.AUDIT_SIGNING_KEYS[0].encode(), digest.encode(), hashlib.sha256).hexdigest()


def verify(event):
    digest, _ = sign(payload(event))
    return hmac.compare_digest(digest, event.content_sha256) and any(
        hmac.compare_digest(hmac.new(key.encode(), digest.encode(), hashlib.sha256).hexdigest(), event.integrity_seal)
        for key in settings.AUDIT_SIGNING_KEYS)

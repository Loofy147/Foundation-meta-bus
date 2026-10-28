"""Raw-body signature verification and durable, idempotent webhook ingress."""
import hashlib
import hmac
import json

class InvalidWebhook(ValueError):
    """Raised when a provider payload fails validation."""
class PersistenceFailure(RuntimeError):
    """Raised when a webhook cannot be durably stored; no acknowledgement is returned."""

def verify_signature(payload, signature_header, app_secret):
    if not isinstance(payload, bytes) or not isinstance(signature_header, str):
        return False
    if not signature_header.startswith("sha256=") or not isinstance(app_secret, (str, bytes)) or not app_secret:
        return False
    secret = app_secret.encode("utf-8") if isinstance(app_secret, str) else app_secret
    expected = "sha256=" + hmac.new(secret, payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_header)

def ingest_signed_payload(payload, signature_header, app_secret, *, normalize, store):
    if not verify_signature(payload, signature_header, app_secret):
        raise InvalidWebhook("invalid webhook signature")
    if not callable(normalize):
        raise InvalidWebhook("provider normalizer is required")
    try:
        document = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InvalidWebhook("signed payload is not valid UTF-8 JSON") from exc
    event = normalize(document)
    if not isinstance(event, dict):
        raise InvalidWebhook("normalizer must return one canonical event")
    sender_id, event_id = event.get("sender_id"), event.get("event_id")
    if not isinstance(sender_id, str) or not sender_id.strip():
        raise InvalidWebhook("sender id is required; identity is never guessed")
    if not isinstance(event_id, str) or not event_id.strip():
        raise InvalidWebhook("stable event id is required")
    try:
        inserted = store.put_if_absent(event)
    except Exception as exc:
        raise PersistenceFailure("event was not durably stored; do not acknowledge it") from exc
    if type(inserted) is not bool:
        raise PersistenceFailure("store must return a boolean insert result")
    return {"status_code": 200, "event_id": event_id, "duplicate": not inserted}

"""Meta-style webhook primitives: subscription handshake, signed bounded POST, batch-safe persistence."""
import hashlib
import hmac
import json

MAX_WEBHOOK_BYTES = 3_000_000


class InvalidWebhook(ValueError):
    """Raised when a provider payload or handshake fails validation."""


class PersistenceFailure(RuntimeError):
    """Raised when a webhook cannot be durably stored; no acknowledgement is returned."""


def verify_subscription(mode, verify_token, expected_token, challenge):
    """Return the provider's challenge only when mode and token are correct.

    The HTTP adapter should return the returned string as a plain-text response.
    """
    if not isinstance(mode, str) or mode != "subscribe":
        raise InvalidWebhook("webhook subscription mode is invalid")
    if not isinstance(verify_token, str) or not verify_token:
        raise InvalidWebhook("webhook verification token is missing")
    if not isinstance(expected_token, str) or not expected_token:
        raise InvalidWebhook("configured webhook verification token is missing")
    if not isinstance(challenge, str) or not challenge:
        raise InvalidWebhook("webhook challenge is missing")
    if not hmac.compare_digest(verify_token.encode("utf-8"), expected_token.encode("utf-8")):
        raise InvalidWebhook("webhook verification token does not match")
    return challenge


def verify_signature(payload, signature_header, app_secret):
    if not isinstance(payload, bytes) or not isinstance(signature_header, str):
        return False
    if not signature_header.startswith("sha256=") or not isinstance(app_secret, (str, bytes)) or not app_secret:
        return False
    secret = app_secret.encode("utf-8") if isinstance(app_secret, str) else app_secret
    expected = "sha256=" + hmac.new(secret, payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_header)


def ingest_signed_payload(payload, signature_header, app_secret, *, normalize, store):
    """Normalize a signed envelope to one event or a list of events and persist idempotently.

    An HTTP adapter should acknowledge only after this function returns. If persistence
    fails partway through a batch, retry is safe only because already stored event IDs
    remain idempotent; the remaining events must also be durably stored before ACK.
    """
    if not isinstance(payload, bytes) or len(payload) > MAX_WEBHOOK_BYTES:
        raise InvalidWebhook("webhook body is missing or exceeds the 3 MB ingress limit")
    if not verify_signature(payload, signature_header, app_secret):
        raise InvalidWebhook("invalid webhook signature")
    if not callable(normalize):
        raise InvalidWebhook("provider normalizer is required")
    try:
        document = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InvalidWebhook("signed payload is not valid UTF-8 JSON") from exc
    normalized = normalize(document)
    if isinstance(normalized, dict):
        events = [normalized]
    elif isinstance(normalized, (list, tuple)) and normalized and all(isinstance(item, dict) for item in normalized):
        events = list(normalized)
    else:
        raise InvalidWebhook("normalizer must return one canonical event or a non-empty list of canonical events")

    # Validate the whole batch before the first write; identity is never guessed.
    seen_ids = set()
    for event in events:
        sender_id, event_id = event.get("sender_id"), event.get("event_id")
        if not isinstance(sender_id, str) or not sender_id.strip():
            raise InvalidWebhook("sender id is required; identity is never guessed")
        if not isinstance(event_id, str) or not event_id.strip():
            raise InvalidWebhook("stable event id is required")
        if event_id in seen_ids:
            # Duplicate delivery IDs within one envelope are tolerated, but the unique
            # store key still ensures they cannot create duplicate persistence records.
            continue
        seen_ids.add(event_id)

    stored = []
    try:
        for event in events:
            stored.append(store.put_if_absent(event))
    except Exception as exc:
        raise PersistenceFailure("batch was not fully durably stored; do not acknowledge it") from exc
    if any(type(value) is not bool for value in stored):
        raise PersistenceFailure("store must return a boolean insert result for every event")
    duplicate_count = sum(1 for value in stored if not value)
    return {
        "status_code": 200,
        "events_accepted": len(events),
        "duplicates": duplicate_count,
        "duplicate": duplicate_count == len(events),
    }

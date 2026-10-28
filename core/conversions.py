"""Policy-gated conversion preparation and injected, deduplicated dispatch."""
from .policy import authorize

class TransportNotConfigured(RuntimeError):
    """Raised when no explicit outbound provider transport was injected."""
class DispatchOutcomeUnknown(RuntimeError):
    """Raised when a send may have reached the provider and requires reconciliation."""

def prepare_conversion(event, policy):
    authorize(policy)
    if not isinstance(event, dict):
        raise ValueError("canonical event is required")
    event_id, name, timestamp = event.get("event_id"), event.get("event_name"), event.get("event_time")
    referral = event.get("referral")
    clid = referral.get("ctwa_clid") if isinstance(referral, dict) else None
    if not isinstance(event_id, str) or not event_id.strip():
        raise ValueError("stable event_id is required for deduplication")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("event_name is required")
    if type(timestamp) is not int or timestamp <= 0:
        raise ValueError("event_time must be a positive integer timestamp")
    if not isinstance(clid, str) or not clid.strip():
        raise ValueError("referral.ctwa_clid is required; fallback identifiers are prohibited")
    payload = {"event_id": event_id, "event_name": name, "event_time": timestamp, "ctwa_clid": clid}
    if "currency" in event:
        currency = event["currency"]
        if not isinstance(currency, str) or len(currency) != 3 or not currency.isalpha() or currency.upper() != currency:
            raise ValueError("currency must be a three-letter uppercase code")
        payload["currency"] = currency
    if "value" in event:
        value = event["value"]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
            raise ValueError("value must be a non-negative number")
        payload["value"] = value
    return payload

def dispatch_conversion(event, policy, *, store, transport=None):
    payload = prepare_conversion(event, policy)
    if transport is None or not callable(getattr(transport, "send", None)):
        raise TransportNotConfigured("external transport is disabled unless explicitly injected")
    if store is None or not callable(getattr(store, "reserve_conversion", None)):
        raise RuntimeError("a durable outbox is required before dispatch")
    event_id = payload["event_id"]
    if not store.reserve_conversion(event_id, payload):
        status = store.get_conversion_status(event_id)
        if status in {"PENDING", "UNKNOWN"}:
            return {"status": "RECONCILIATION_REQUIRED", "sent": False}
        return {"status": "DUPLICATE", "sent": False}
    try:
        transport.send(payload)
    except Exception as exc:
        try:
            store.mark_conversion_outcome(event_id, "UNKNOWN")
        except Exception as persist_exc:
            raise DispatchOutcomeUnknown("send outcome and outbox update are both uncertain") from persist_exc
        raise DispatchOutcomeUnknown("send outcome is unknown; automatic retry is prohibited") from exc
    try:
        store.mark_conversion_outcome(event_id, "SENT")
    except Exception as exc:
        raise DispatchOutcomeUnknown("provider may have accepted event but SENT was not durably recorded") from exc
    return {"status": "SENT", "sent": True}

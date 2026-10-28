"""Outbound consent and service-window guards. No provider calls are made here."""
from datetime import datetime
from .policy import PolicyDenied, authorize

def require_opt_in(purpose, granted_purposes):
    if not isinstance(purpose, str) or not purpose.strip():
        raise PolicyDenied("a named consent purpose is required")
    granted = {item for item in (granted_purposes or []) if isinstance(item, str)}
    if purpose not in granted:
        raise PolicyDenied(f"explicit opt-in is missing for purpose {purpose}")
    return True

def authorize_outbound_message(*, kind, purpose, now, last_inbound_at, granted_purposes, policy):
    authorize(policy)
    if kind not in {"freeform", "template"}:
        raise PolicyDenied("unknown outbound message kind")
    if kind == "template" or purpose == "marketing":
        require_opt_in(purpose, granted_purposes)
    if kind == "freeform":
        if not isinstance(now, datetime) or not isinstance(last_inbound_at, datetime):
            raise PolicyDenied("message window timestamps are required")
        if now.tzinfo is None or last_inbound_at.tzinfo is None:
            raise PolicyDenied("message window timestamps must be timezone-aware")
        hours = (now - last_inbound_at).total_seconds() / 3600
        if hours < 0 or hours > 24:
            raise PolicyDenied("freeform reply is outside the 24-hour service window")
    return True

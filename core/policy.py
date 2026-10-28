"""Fail-closed operation authorization."""
class PolicyDenied(PermissionError):
    """Raised whenever operation authorization cannot be proven."""

def authorize(policy):
    if not isinstance(policy, dict):
        raise PolicyDenied("missing policy; default is DENY")
    state = policy.get("state", "DENY")
    if state != "ALLOW":
        raise PolicyDenied(f"operation is not allowed (state={state})")
    owner, decided_on, evidence = policy.get("owner"), policy.get("decided_on"), policy.get("evidence")
    if not isinstance(owner, str) or not owner.strip():
        raise PolicyDenied("ALLOW policy has no accountable owner")
    if not isinstance(decided_on, str) or not decided_on.strip():
        raise PolicyDenied("ALLOW policy has no decision date")
    if not isinstance(evidence, list) or not evidence:
        raise PolicyDenied("ALLOW policy has no evidence")
    return True

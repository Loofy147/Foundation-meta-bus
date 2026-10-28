#!/usr/bin/env python3
"""Validate system.json with explicit mutation tests for the safety rules."""
import copy
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
STATES = {"DENY", "APPROVAL_REQUIRED", "ALLOW"}
CRITICAL_POLICIES = {"P-CAPI-DISPATCH", "P-DATA-EXTERNAL", "P-LLM-HOSTED", "P-PROFILE-BUILD", "P-MODEL-TRAIN"}

def load():
    with (HERE / "system.json").open("r", encoding="utf-8") as handle:
        spec = json.load(handle)
    with (HERE / "registry.json").open("r", encoding="utf-8") as handle:
        registry = json.load(handle)
    return spec, registry

def check(spec, registry):
    failures = []
    def fail(rule, message): failures.append((rule, message))
    collections = [("providers", spec.get("providers", [])), ("policies", spec.get("policies", [])),
                   ("operations", spec.get("operations", [])), ("workflows", spec.get("workflows", [])),
                   ("data_classes", spec.get("data_classes", [])), ("invariants", spec.get("invariants", []))]
    for name, rows in collections:
        ids = [row.get("id") for row in rows]
        if any(not isinstance(value, str) or not value.strip() for value in ids) or len(ids) != len(set(ids)):
            fail("S1", f"{name} must have non-empty unique ids")
    providers = {x.get("id"): x for x in spec.get("providers", [])}
    policies = {x.get("id"): x for x in spec.get("policies", [])}
    operations = {x.get("id"): x for x in spec.get("operations", [])}
    data_classes = {x.get("id") for x in spec.get("data_classes", [])}
    capabilities = {x.get("id") for x in registry.get("capabilities", [])}
    for provider in spec.get("providers", []):
        for capability in provider.get("capabilities", []):
            if capability not in capabilities:
                fail("S2", f"provider {provider.get('id')} references unknown capability {capability}")
    for operation in spec.get("operations", []):
        policy = policies.get(operation.get("policy"))
        if operation.get("provider") not in providers:
            fail("S3", f"operation {operation.get('id')} references unknown provider {operation.get('provider')}")
        if policy is None:
            fail("S3", f"operation {operation.get('id')} references unknown policy {operation.get('policy')}")
        elif policy.get("operation") != operation.get("id"):
            fail("S3", f"policy {policy.get('id')} is not bound to operation {operation.get('id')}")
        for data_class in operation.get("data_classes", []):
            if data_class not in data_classes:
                fail("S3", f"operation {operation.get('id')} references unknown data class {data_class}")
        if operation.get("direction") not in {"inbound", "outbound", "internal"}:
            fail("S3", f"operation {operation.get('id')} has invalid direction")
        if operation.get("transport") not in {"none", "injected"}:
            fail("S7", f"operation {operation.get('id')} has unsupported transport")
        if operation.get("external_effect") and operation.get("transport") != "injected":
            fail("S7", f"external operation {operation.get('id')} must use injected transport")
        if (operation.get("direction") == "outbound" and operation.get("external_effect")
                and "Z1_BUSINESS_MESSAGE" in operation.get("data_classes", [])
                and policy is not None and policy.get("state") == "ALLOW"):
            fail("S8", f"outbound operation {operation.get('id')} with business-message data cannot be ALLOW in this baseline")
    for policy in spec.get("policies", []):
        state = policy.get("state")
        if state not in STATES:
            fail("S4", f"policy {policy.get('id')} has invalid authorization state {state}")
        if state == "ALLOW":
            if not isinstance(policy.get("owner"), str) or not policy["owner"].strip():
                fail("S4", f"ALLOW policy {policy.get('id')} has no accountable owner")
            if not isinstance(policy.get("decided_on"), str) or not policy["decided_on"].strip():
                fail("S4", f"ALLOW policy {policy.get('id')} has no decision date")
            if not isinstance(policy.get("evidence"), list) or not policy["evidence"]:
                fail("S4", f"ALLOW policy {policy.get('id')} has no evidence")
    limits = spec.get("limits", {})
    limit = limits.get("max_webhook_payload_bytes")
    if type(limit) is not int or limit != 3_000_000:
        fail("S9", "max_webhook_payload_bytes must equal 3,000,000")
    if spec.get("default_authorization") != "DENY":
        fail("S5", "default_authorization must remain DENY")
    for required in CRITICAL_POLICIES:
        policy = policies.get(required)
        if policy is None:
            fail("S5", f"required safety policy {required} is missing")
        elif policy.get("state") == "ALLOW":
            fail("S5", f"critical safety policy {required} must remain DENY")
    webhook = next((x for x in spec.get("workflows", []) if x.get("id") == "inbound_webhook"), None)
    required_steps = ["verify_signature", "require_sender_id", "persist_idempotently", "acknowledge_200"]
    if webhook is None:
        fail("S6", "inbound_webhook workflow is missing")
    else:
        steps = webhook.get("steps", [])
        positions = [steps.index(step) if step in steps else None for step in required_steps]
        if any(position is None for position in positions) or positions != sorted(positions):
            fail("S6", "webhook must verify signature, require sender, persist, then acknowledge in order")
    for workflow in spec.get("workflows", []):
        if workflow.get("operation") not in operations:
            fail("S6", f"workflow {workflow.get('id')} references unknown operation")
        if "send_direct_network" in workflow.get("steps", []):
            fail("S7", f"workflow {workflow.get('id')} contains a prohibited direct-network step")
    transport = spec.get("transport_policy", {})
    if transport.get("network_calls_from_core") is not False:
        fail("S7", "core network calls must remain disabled")
    return failures

def mutations(spec, registry):
    def mutate(name, rule, fn):
        changed_spec, changed_registry = copy.deepcopy(spec), copy.deepcopy(registry)
        fn(changed_spec, changed_registry)
        return name, rule, changed_spec, changed_registry
    def policy(s, key): return next(p for p in s["policies"] if p["id"] == key)
    def provider(s, key): return next(p for p in s["providers"] if p["id"] == key)
    def workflow(s, key): return next(p for p in s["workflows"] if p["id"] == key)
    return [
        mutate("remove critical conversion policy", "S5", lambda s, r: s.update(policies=[p for p in s["policies"] if p["id"] != "P-CAPI-DISPATCH"])) ,
        mutate("reference unknown capability", "S2", lambda s, r: provider(s, "whatsapp_cloud_api")["capabilities"].append("NO-SUCH-CAPABILITY")),
        mutate("default authorization becomes ALLOW", "S5", lambda s, r: s.update(default_authorization="ALLOW")),
        mutate("ALLOW policy loses accountability/evidence", "S4", lambda s, r: policy(s, "P-WEBHOOK-INGEST").update(owner=None, decided_on=None, evidence=[])),
        mutate("critical conversion policy enabled", "S5", lambda s, r: policy(s, "P-CAPI-DISPATCH").update(state="ALLOW", owner="role:test", decided_on="2026-10-28", evidence=[{"kind":"test", "ref":"synthetic"}])),
        mutate("acknowledgement moved before persistence", "S6", lambda s, r: workflow(s, "inbound_webhook").update(steps=["verify_signature", "normalize_payload", "require_sender_id", "acknowledge_200", "persist_idempotently"])),
        mutate("remove webhook payload size limit", "S9", lambda s, r: s.update(limits={"max_webhook_payload_bytes": None}))
    ]

def selftest(spec, registry):
    baseline = set(check(spec, registry))
    output = []
    for name, rule, changed_spec, changed_registry in mutations(spec, registry):
        after = check(changed_spec, changed_registry)
        caught = any(found_rule == rule and message not in {m for r, m in baseline if r == rule} for found_rule, message in after)
        output.append((name, rule, caught))
    return output

def main():
    spec, registry = load()
    failures = check(spec, registry)
    for rule, message in failures: print(f"FAIL {rule}: {message}")
    tests = selftest(spec, registry)
    for name, rule, caught in tests: print(f"{'caught' if caught else 'MISSED':7} {rule}: {name}")
    missed = [test for test in tests if not test[2]]
    print(f"SPEC: {len(failures)} FAIL; self-test {len(tests) - len(missed)}/{len(tests)} mutants detected")
    raise SystemExit(1 if failures or missed else 0)

if __name__ == "__main__": main()

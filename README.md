# Foundation-meta-bus

Evidence-backed capability registry, planning engine and fail-closed runtime foundation for integrating Meta messaging, Conversions API, commerce, logistics and payment providers for a business operating in Algeria.

## One command

Use Python 3.12 or later:

```bash
python3 gate.py --full
```

This rebuilds the registry, system specification and planning data, runs structural checks, plan mutations/contracts, unit tests and source mutation tests. Tests make no live provider calls. `python3 gate.py --write-results` refreshes the generated `results*.txt`; `python3 gate.py --verify-results` reruns the full gate and fails if a committed report is missing, empty or differs.

## Source of truth

Authored files: `A_data.json`, `build_registry.py`, `check.py`, `build_spec.py`, `check_spec.py`, `build_plan.py`, `plan.py`, `core/`, `tests/`, `gate.py`.

Generated files: `registry.json`, `claims.json`, `system.json`, `assumptions.json`, `roadmap.json`, `meta_docs_map.json`, and `results*.txt`. Edit authored sources and regenerate derived artifacts.

## Current safety posture

- Unknown, missing or incomplete policy authorizations fail closed.
- Conversion dispatch, external customer-data sharing, hosted LLM processing, contact profiling and training on business conversations are denied in the authored specification.
- Outbound messages, courier parcel creation, payment links and commerce writes require explicit approval.
- Webhook ingress verifies the raw-body signature, rejects missing identity, writes idempotently before acknowledging, and never guesses who sent a message.
- External effects need an injected transport. An ambiguous conversion send becomes `UNKNOWN` and cannot be automatically retried.
- Payload storage requires injected sealing/opening callbacks. The test codec is synthetic and is not cryptographic.

## Still required before real production data

The code gate does not establish Meta account eligibility, current Algeria-specific billing/pricing, legal permission, current provider contracts, live referral preservation, service availability, or successful live delivery. Those remain OPEN until supported by source-backed checks or controlled experiments. Counsel owns legal determinations and policy approvals. Production deployment also needs reviewed authenticated encryption and key management, retention/deletion controls, access controls, monitoring and incident recovery.

Accountability values such as `role:engineering` and `role:algerian-counsel` identify functions, not named individuals; the project must assign and accept individual ownership before operating the system.

## Review

- [Integration pull request](https://github.com/Loofy147/Foundation-meta-bus/pull/1)
- [Gate reconstruction record](docs/audits/gate-reconstruction-2026-10-28.md)
- [Original Dropbox guidance](docs/reference/dropbox-archive/AGENTS.md)

## Current external research

- [Meta / WhatsApp research checkpoint, evidence and unresolved gates](docs/research/meta-platform-check-2026-10-28.md)

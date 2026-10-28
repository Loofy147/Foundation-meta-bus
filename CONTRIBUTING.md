# Contributing to Foundation-meta-bus

## Required gate

Run `python3 gate.py --full` using Python 3.12 or later. It must pass before a change is proposed for merge. Do not treat a code gate as proof of live provider readiness.

## Authored vs generated files

| Authored sources | Generated outputs |
|---|---|
| `A_data.json`, `build_registry.py`, `check.py` | `registry.json`, `claims.json` |
| `build_spec.py`, `check_spec.py` | `system.json` |
| `build_plan.py`, `plan.py` | `assumptions.json`, `roadmap.json`, `meta_docs_map.json` |
| `core/`, `tests/`, `gate.py`, documentation | `results*.txt` |

Change source and regenerate derived data. Do not hand-edit generated outputs as the sole fix.

## Evidence rules

- Evidence grades are PROVEN, SUPPORTED, OPEN and CONTRADICTED. Never promote a claim without a new source-backed record, final source URL and retrieval date.
- An inherited READY label is not independent verification.
- Keep evidence tied to the specific capability, integration path and conditions it actually supports.
- Assumptions need falsification tests, roadmap items and accountable functions. A role assignment does not prove that a named individual accepted responsibility.
- Counsel owns legal conclusions and policy-table decisions. Tests may use synthetic authorization objects; they must not change production policy to ALLOW.

## Runtime and data rules

- Never commit real credentials, API tokens, app secrets, phone numbers, names or customer message text.
- No code or test calls Meta, a courier, payment provider, LLM API or other external service. All external transports are injected explicitly.
- Missing or uncertain authorization means DENY. Do not add a default network transport.
- Reject missing sender identity. Do not infer identity from a previous, first or nearby contact.
- Persist webhook events before acknowledging. Duplicate delivery must remain idempotent.
- A conversion requires its own `referral.ctwa_clid`; do not invent fallback identifiers. An ambiguous send must not be retried automatically.
- `SQLiteStore` requires injected sealing/opening functions. The test codec is NOT encryption and must never process real data. Production requires reviewed authenticated encryption, key management, retention/deletion, access control, monitoring and recovery.

## Reporting template

```text
What changed:
Evidence and source URLs/dates:
Assumptions tested or changed:
Commands run and observed result:
Still OPEN:
Not run:
```

The partial Dropbox archive is reference material, not a complete original source tree. Reconstructed implementation is identified as new authored code rather than claimed recovered source.

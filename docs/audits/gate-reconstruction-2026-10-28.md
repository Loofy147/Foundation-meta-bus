# Gate reconstruction record — 2026-10-28

## Scope

The archived ZIP did not contain `build_spec.py`, `check_spec.py`, `system.json`, `core/` or the source mutation runner. The new components below are a reconstruction from the archived operating contract and current registry, not recovered original source code.

## Added implementation

- `build_spec.py` and generated `system.json`: providers, operation map, data classes, conservative policies, workflow order and safety invariants.
- `check_spec.py`: structural and authorization checks plus six mutation self-tests.
- `core/policy.py`: fail-closed authorization.
- `core/consent.py`: purpose opt-in and time-window checks.
- `core/webhook.py`: raw HMAC signature verification, identity checks and acknowledgement only after durable storage.
- `core/store.py`: SQLite idempotency and conversion outbox, requiring injected payload sealing/opening callbacks.
- `core/conversions.py`: `ctwa_clid`-required conversion preparation, injected transport, outbox reservation and no automatic retry after an ambiguous send.
- `tests/test_core.py`, `tests/test_spec.py`, `tests/mutate.py`: synthetic-data unit and mutation coverage.
- `gate.py`: a single source-level gate; strict report verification refuses missing or empty results.
- Planning fixes: explicit failure branches for A-03, A-10 and A-19; tests for the branches; accountability roles for all 21 assumptions.
- Registry metadata fix: `generated` is now separate from the last evidence verification date. This metadata change does not claim new provider research.

## Authorization and privacy posture

Conversion dispatch, third-party customer-data sharing, hosted LLM processing, cross-message contact profiling and training on business conversations remain `DENY`. Message sends, courier parcel creation, payment links and commerce writes remain `APPROVAL_REQUIRED`. Only local webhook-ingress processing is represented as `ALLOW`, with code-level evidence.

`SQLiteStore` has no default plaintext codec. Tests use a deliberately synthetic reversible codec; it is NOT suitable for actual personal data. Before real production data is processed, the deployment must provide audited authenticated encryption/key management and deletion, retention, access-control, monitoring and recovery controls.

## Not proven by source-level tests

Account eligibility, current Meta terms/pricing, Algeria-specific billing, business verification, legal interpretations, live referral preservation, provider contracts, live webhook delivery, courier/PSP operations and business outcomes remain OPEN. Account-specific and legal outcomes must not be inferred from a green code gate.

## Validation state

The commit containing this record must be evaluated by GitHub Actions. The exact run ID, tested commit, job outcome and any residual failures should be appended only after the remote run is observed. Do not call this production-ready before that evidence and external prerequisites are closed.

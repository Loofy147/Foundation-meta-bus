# Agent guidance

Read `CONTRIBUTING.md` first. The repository’s authored files and reproducible outputs outrank conversation summaries and archived snapshots.

## Required loop

1. Inspect current source, branch head and source evidence.
2. Separate proven implementation behavior from current provider, account, commercial and legal assumptions.
3. Change authored code, then rebuild generated data.
4. Run `python3 gate.py --full`; inspect the actual result.
5. Report proven, supported, open, failed and not-run items separately.

## Non-negotiable controls

- Never invent sources, dates, owners, test outcomes, legal conclusions, prices or provider behavior.
- No claim is promoted without a new source-backed record and a corresponding scope.
- Missing policies, unknown states, absent approvals or absent transports deny by default.
- No real credentials or personal/customer data in tests or logs. No network calls from code or tests.
- Do not change counsel-owned policy decisions to ALLOW in order to pass a gate.
- Never guess sender identity or synthesize an attribution/referral identifier.
- Webhook persistence must finish before acknowledgement. Delivery must be idempotent.
- An ambiguous external send is `UNKNOWN`, not safe to retry.
- Test encryption callbacks are synthetic only. Real data processing remains blocked until an audited authenticated-encryption/key-management lifecycle and retention/deletion controls are deployed.
- Function-level owner labels are not evidence of a named person accepting ownership.

## Reporting

```text
Done:
Proven (command or primary source):
Supported:
OPEN (assumption ids):
Failed:
Not run:
Next action and required resource:
```

The original Dropbox guidance is preserved under `docs/reference/dropbox-archive/`.

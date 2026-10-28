# Integration validation evidence — 2026-10-28

## Scope

This record captures the observed validation of the Dropbox-derived registry/planning integration in branch `integration/dropbox-planning-layer-2026-10-28`. It is not a production-readiness certificate and does not claim the wider `gate.py --full` passed.

## Input artifact

- Repository: `Loofy147/Foundation-meta-bus`
- ZIP: `files - 2026-10-28T093522.822.zip`
- ZIP blob SHA: `1228a7b5eec3ee0cb7722f186a790bd4b7157d93`
- Archive integrity: 10 ZIP members decompressed; all uncompressed sizes and CRC-32 values matched the central directory.
- Registry records in the Dropbox snapshot: 43 capabilities, 44 source URLs, no duplicate IDs.
- Original main registry: 37 capabilities.
- Reconciliation: added M1, T1, C0, X1, O1, TP1; updated B2, B4, F1, F2, F3.
- A static source projection of the reconciled generator and registry matched the archived JSON object, including ordering. The actual Python generation result was then checked by CI.

Full reconciliation record: [Dropbox / GitHub reconciliation report](https://github.com/Loofy147/Foundation-meta-bus/blob/audit/dropbox-reconciliation-2026-10-28/docs/audits/dropbox-reconciliation-2026-10-28.md).

## Latest observed CI execution

- Workflow: Foundation registry and planning validation
- Run number: 10
- Run ID: 40661373817
- Result: **completed / success**
- Job: `validate`, job ID `122724951209`
- Tested code head: `10bc6347586a3de81ce9b441caec0227f5c39f4c`
- Run link: https://github.com/Loofy147/Foundation-meta-bus/actions/runs/40661373817
- After that successful run, documentation-only commit `88ed8a36e270a126330dc9b15cc0e0f1c3b1c716` added this evidence record. That commit did not change source code, tests, workflow, or generated data; no separate workflow run was returned for that documentation-only commit.

Observed completed steps:
1. Checkout and Python setup
2. Python compile check
3. Registry rebuild
4. Registry integrity check and claims ledger refresh
5. Planning-data rebuild
6. Plan structural check
7. Plan mutation self-tests and scenario contracts
8. Unit tests
9. Generated-artifact reproducibility check (`git diff --exit-code` over registry/claims/planning JSON)

Observed outputs:
- Registry integrity rules R1, R2, R3, R5 and R6: **pass**
- Plan structure: **0 failures, 4 warnings**
- Plan mutation self-tests: **12/12 behaved as expected**
- Scenario contracts: **21/21 hold**
- Unit tests: **6 passed** (`Ran 6 tests`, `OK`)
- Generated artifacts: reproducibility step completed successfully.
- After the follow-up fixes, the log no longer showed the previous Python `ResourceWarning`s for unclosed JSON files or the earlier Node.js 20 deprecation warning from the workflow's action versions.

These results are supported by the remote GitHub Actions run and its job logs. The run is reproducible through the committed workflow on the branch head at the time of the run.

## Warnings that remain intentionally visible

1. Registry checker: 14 original artefact capabilities still carry READY labels without independent verification.
2. Planning checker:
   - P5: A-03, A-10 and A-19 have no scenario defining their `fails` outcome.
   - P8: 21 assumptions do not have an owner.
3. All 21 assumptions remain OPEN. Owners are not auto-assigned because that would invent a decision owner.

These are warnings, not hidden successes. They should be resolved with evidence and explicit decisions; the checks must not be weakened to make the report green.

## What this CI run does not establish

The ZIP and the current repository still do not provide the following expected production-gate dependencies: `build_spec.py`, `check_spec.py`, `system.json`, `core/`, and the wider mutation-test sources. As a result:

- `gate.py --full`: **NOT RUN / NOT AVAILABLE from current dependency closure**
- `gate.py --verify-results`: **NOT RUN / NOT AVAILABLE from current dependency closure**
- Live Meta API/account eligibility, current Algeria-specific rates, courier/payment-provider operations, and legal determinations: **not tested by this workflow**

The current workflow is deliberately named and scoped as registry/planning validation. A successful result must not be reported as full system or production readiness.

## Change control

- Draft PR: https://github.com/Loofy147/Foundation-meta-bus/pull/1
- Head branch: `integration/dropbox-planning-layer-2026-10-28`
- The PR remains draft and unmerged until its latest CI status and review are accepted.

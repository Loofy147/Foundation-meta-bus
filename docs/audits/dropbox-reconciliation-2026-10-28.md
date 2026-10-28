# Dropbox / GitHub reconciliation checkpoint — 2026-10-28

## Status

**Audit checkpoint only. No application code or generated registry was changed in this commit.** This report records a read-only comparison of the GitHub main snapshot and the Dropbox archive's text-extracted contents. It does not claim the archive's full ZIP directory was inspected or that any test command was executed.

## Sources and provenance

### GitHub repository

- Repository: Loofy147/Foundation-meta-bus
- Observed default branch: main
- Observed latest commit at audit start: [4a264252c0cd0b15df9220e60f61c42640233e40](https://github.com/Loofy147/Foundation-meta-bus/commit/4a264252c0cd0b15df9220e60f61c42640233e40), titled **Add files via upload**, committed 2026-10-18 19:58:35 UTC.
- Recent-commit query returned two commits for the repository.
- The commit status lookup returned an empty status list. The available workflow-run lookup also returned no rows; that lookup is scoped to PR-triggered runs, so this is **not** proof that no other workflow runs ever existed.
- Key blob identities observed:
  - A_data.json: 93fb8a05ffc090b13fead0341a7055c0dcf04aa
  - build_registry.py: e110a19ae1b43b760faa761867c8d647abaa7340
  - registry.json: 620e0cb5843df9d8d6ee6c5243ffed1c16896cb1
  - check.py: 59dc7096761aa643aef1460d5bf059c6b860ca8c
  - results.txt: d12b7e34cf6b9127c4065693010bce05066c476d

References: [A_data.json](https://github.com/Loofy147/Foundation-meta-bus/blob/main/A_data.json), [build_registry.py](https://github.com/Loofy147/Foundation-meta-bus/blob/main/build_registry.py), [registry.json](https://github.com/Loofy147/Foundation-meta-bus/blob/main/registry.json), [check.py](https://github.com/Loofy147/Foundation-meta-bus/blob/main/check.py), [results.txt](https://github.com/Loofy147/Foundation-meta-bus/blob/main/results.txt).

### Dropbox archive

- Name: files - 2026-10-28T093522.822.zip
- Display path: /files - 2026-10-28T093522.822.zip
- Reported size: 47,569 bytes (46.45 KiB)
- Dropbox-reported server modification time: 2026-10-28 08:39:29 UTC
- Dropbox content_hash returned by its download-link metadata: 4f6935bdb7de5be1dcda84385fd792c36101a1e44716576df879cd381a30d84a. This value is recorded as Dropbox's content hash, **not** as an independently computed SHA-256.
- The Dropbox text-extraction interface yielded 159,985 characters and ten named content blocks: CONTRIBUTING.md, AGENTS.md, results_plan.txt, assumptions.json, roadmap.json, meta_docs_map.json, plan.py, gate.py, build_plan.py, and registry.json.
- **Limitation:** the raw ZIP bytes and central-directory listing were not available in the working container. Therefore, files not exposed by text extraction are classified as **not evidenced by the extracted view**, not conclusively absent from the ZIP.

## Finding F-01 — Registry versions diverge (HIGH)

| Check | GitHub main | Dropbox extracted registry |
|---|---:|---:|
| registry.json capability records | 37 | 43 |
| Registry generated field | 2026-10-18 | 2026-10-18 |
| IDs unique in parsed capability list | Yes | Yes |

The current GitHub A_data.json contains 29 original capabilities. The current build_registry.py declares eight added capability records: P1, P2, L1, K1, K2, S1, P3, and D6. This static source inventory aligns with the 37 IDs in the current GitHub registry. **The generator was not executed in this audit**, so this is a source/ID comparison rather than a reproducibility result.

The Dropbox registry contains six additional IDs not present in the GitHub registry:

| ID | Name | Dropbox registry state | Evidence date |
|---|---|---|---|
| M1 | WhatsApp messaging channel (Cloud API or BSP) | CONFIG; checked=false | 2026-10-24 |
| T1 | Cloud API test environment (test WABA and test number) | CONFIG; checked=true | 2026-10-24 |
| C0 | Messaging cost model | CONFIG; checked=true | 2026-10-24 |
| X1 | WhatsApp Business Solution Terms constraints | CONFIG; checked=true | 2026-10-24 |
| O1 | Messaging policy and opt-in | CONFIG; checked=true | 2026-10-24 |
| TP1 | Tech Provider multi-tenant onboarding | CONFIG; checked=true | 2026-10-24 |

The extra records have evidence and dependency metadata in the Dropbox registry. They must not be added by hand to generated registry.json only. Their authored definitions must be preserved in the relevant source generator(s), and the generated output must then be rebuilt and checked.

### Date semantics requiring resolution

Both registry snapshots report generated: 2026-10-18, while the six additional Dropbox records carry verified_on: 2026-10-24. The GitHub generator hardcodes VERIFIED_ON = 2026-10-18. This makes generated unsuitable as a verified build timestamp unless the project explicitly defines it as a fixed evidence-baseline date. Separate build time from evidence-review time, or document the existing field's precise meaning.

## Finding F-02 — Full gate dependency closure is not established (HIGH)

The extracted gate.py declares these steps:

1. build registry — build_registry.py
2. check registry — check.py
3. build spec — build_spec.py
4. check spec and its mutation self-test — check_spec.py
5. build planning data — build_plan.py
6. validate plan — plan.py --check
7. run plan self-tests and scenario contracts — plan.py --selftest
8. run unit tests — python -m unittest discover -s tests -t .

The --full mode adds tests/mutate.py. The --verify-results mode additionally rebuilds recorded outputs and compares them with committed non-empty files.

The extracted text view does not expose an updated build_registry.py, build_spec.py, check.py, check_spec.py, or the core/ and tests/ file contents. GitHub main does expose build_registry.py and check.py, but the specific source needed to produce the six extra Dropbox capabilities is not in the current generator. The raw ZIP directory must be inspected before classifying the other items as definitively missing from Dropbox.

**Consequence:** the complete gate's executable dependency closure has not yet been demonstrated. No claim that gate.py --full passes is supported at this checkpoint.

## Finding F-03 — Recorded plan has unresolved warnings (MEDIUM)

The Dropbox results_plan.txt **records** the following output; it was not regenerated in this audit:

- Plan rules: 0 failures, 4 warnings.
- P5 warnings: load-bearing assumptions A-03, A-10, and A-19 have no explicit scenario for their fails outcome.
- P8 warning: 21 assumptions have no owner.
- Recorded plan self-test: 12/12 behaved as expected.
- Recorded scenario contracts: 21/21 hold.
- Parsed planning data: 30 roadmap items, 21/21 assumptions OPEN, 21/21 assumptions unowned, 30 documentation-map entries, and 6 HIGH-priority NOT_READ entries.

These are **reported artefact contents**, not independent test results. The missing assumption owners are an ownership decision, not a field to populate speculatively. P5 warnings should be resolved by defining the consequence of failure or documenting a justified exception—not by weakening the rule.

## Required reconciliation sequence

1. **Preserve the two states.** Keep current GitHub main as the repository baseline; retain the Dropbox archive as an additional source snapshot. Do not overwrite one with the other.
2. **Resolve ZIP inventory.** Obtain a raw ZIP member listing and compute a local SHA-256 from the actual bytes. Compare the exact authored and generated file paths. The connector's extracted text alone is not a full archive manifest.
3. **Restore authored source before generated output.** Locate or reconstruct the source definitions for M1, T1, C0, X1, O1, and TP1; update the generator and the appropriate spec/planning source. Do not edit generated registry.json, assumptions.json, roadmap.json, or meta_docs_map.json as a substitute for rebuilding.
4. **Rebuild and reconcile.** Require the generator's capability IDs and substantive records to match the intended 43-record registry; check uniqueness, evidence grades, checked/evidence consistency, dependency references, and cycles. Make the evidence-date/build-date semantics explicit.
5. **Close the gate's dependencies.** Confirm all scripts, core/, and tests/ required by gate.py exist and are versioned. Ensure the gate stops on any failed command and no reported output is empty.
6. **Run the documented validation in a clean environment.** Run python3 gate.py --full, then python3 gate.py --verify-results after results have been deliberately regenerated and reviewed. Retain real outputs and an environment fingerprint. These commands have **not** been run during this audit.
7. **Only then open a merge request.** Keep this reconciliation branch separate from main until the registry, source generators, plan and full test gate agree.

## Evidence classification

- **Observed directly:** GitHub file contents and blob SHAs listed above; repository commit query; current 37-record GitHub registry; 43-record Dropbox-extracted registry; the six additional IDs; the extracted plan data and recorded warnings.
- **Not independently reproduced:** generator output, registry integrity test, plan test, scenario contracts, unit tests, mutation tests and results-file comparison.
- **OPEN:** exhaustive raw ZIP member inventory; whether the archive contains unexposed test/spec files; a reproducible 43-record build from authored sources; full gate result; any live Meta account/API behavior or legal eligibility.

## Audit branch

This checkpoint is intended for branch audit/dropbox-reconciliation-2026-10-28. It documents discrepancies and next validation gates; it does not change production logic.

# Dropbox / GitHub reconciliation checkpoint — 2026-10-28

## Status

This is a source-reconciliation audit, not a production-readiness certification. The uploaded ZIP has now been read from its GitHub blob, its central directory parsed, and all ten entries decompressed. Every entry's decompressed size and CRC-32 match the ZIP central-directory metadata. No application code or generated registry was changed by this audit commit.

## Evidence objects

### GitHub repository

- Repository: `Loofy147/Foundation-meta-bus`
- Default branch: `main`
- Latest observed main commit: [`eccc2c79402983ae99537d6a4e1f17beb4f72f5e`](https://github.com/Loofy147/Foundation-meta-bus/commit/eccc2c79402983ae99537d6a4e1f17beb4f72f5e), message `Add files via upload`, created 2026-10-28 08:51:17 UTC.
- The commit's changed-file list contains one item: `files - 2026-10-28T093522.822.zip`.
- GitHub file/blob SHA for that ZIP: `1228a7b5eec3ee0cb7722f186a790bd4b7157d93`.
- Commit-status query returned an empty status list. The available workflow-run lookup returned no rows; that lookup is scoped to PR-triggered runs, so this is not proof that no workflow runs have ever existed.
- The current GitHub source blobs inspected:
  - `A_data.json`: `93fb8a05ffc0909b13fead0341a7055c0dcf04aa`
  - `build_registry.py`: `e110a19ae1b43b760faa761867c8d647abaa7340`
  - `registry.json`: `620e0cb5843df9d8d6ee6c5243ffed1c16896cb1`
  - `check.py`: `59dc7096761aa643aef1460d5bf059c6b860ca8c`
  - `results.txt`: `d12b7e34cf6b9127c4065693010bce05066c476d`

References: [main ZIP commit](https://github.com/Loofy147/Foundation-meta-bus/commit/eccc2c79402983ae99537d6a4e1f17beb4f72f5e), [A_data.json](https://github.com/Loofy147/Foundation-meta-bus/blob/main/A_data.json), [build_registry.py](https://github.com/Loofy147/Foundation-meta-bus/blob/main/build_registry.py), [registry.json](https://github.com/Loofy147/Foundation-meta-bus/blob/main/registry.json), [check.py](https://github.com/Loofy147/Foundation-meta-bus/blob/main/check.py), [results.txt](https://github.com/Loofy147/Foundation-meta-bus/blob/main/results.txt).

### Dropbox source object

- Name: `files - 2026-10-28T093522.822.zip`
- Dropbox path: `/files - 2026-10-28T093522.822.zip`
- Reported size: 47,569 bytes (46.45 KiB)
- Server-modified time: 2026-10-28 08:39:29 UTC
- Dropbox content-hash field: `4f6935bdb7de5be1dcda84385fd792c36101a1e44716576df879cd381a30d84a`. This is recorded as Dropbox's content-hash value; it is not claimed to be a locally calculated conventional SHA-256.
- The GitHub ZIP payload decoded to exactly 47,569 bytes and 10 central-directory entries. The entry CRC-32 values below were calculated from the extracted bytes and matched the ZIP metadata for all entries.

| ZIP member | Uncompressed bytes | CRC-32 | Integrity |
|---|---:|---|---|
| `CONTRIBUTING.md` | 6,778 | `10e63520` | PASS |
| `AGENTS.md` | 5,173 | `ab1c64bc` | PASS |
| `results_plan.txt` | 12,642 | `177ee17e` | PASS |
| `assumptions.json` | 11,463 | `9a4699a8` | PASS |
| `roadmap.json` | 12,943 | `308656bb` | PASS |
| `meta_docs_map.json` | 11,778 | `aa9e2933` | PASS |
| `plan.py` | 14,270 | `f6253335` | PASS |
| `gate.py` | 4,208 | `5b48131c` | PASS |
| `build_plan.py` | 26,343 | `2a440fde` | PASS |
| `registry.json` | 54,211 | `92bf5494` | PASS |

This member list is conclusive for the ZIP stored in GitHub; it contains no other files or directory entries.

## Finding F-01 — The uploaded object is a ZIP archive, not an extracted project (HIGH)

The main commit adds only the archive. Its ten members provide guidelines, planning code/data and a generated registry snapshot. The archive itself does **not** contain `build_registry.py`, `check.py`, `build_spec.py`, `check_spec.py`, the `core/` directory, or the `tests/` directory. It also does not contain `claims.json`, `system.json`, `results.txt`, `results_spec.txt`, or `results_core.txt`.

The current repository's existing `build_registry.py` and `check.py` remain available at their normal root paths, but the current source generator does not contain the six new capability definitions or the newer evidence revisions described below. Root-path checks against GitHub's content API returned not found for `build_spec.py`, `check_spec.py`, `tests/mutate.py`, and `system.json`.

## Finding F-02 — Registry divergence is 6 new IDs plus 5 updated records (HIGH)

| Check | Current GitHub `registry.json` | Dropbox ZIP `registry.json` |
|---|---:|---:|
| Capability records | 37 | 43 |
| Duplicate capability IDs | 0 | 0 |
| Evidence entries | — | 80 |
| Status counts | — | 14 READY, 25 CONFIG, 2 UNVERIFIED, 2 BLOCKED |

The current GitHub generator has 29 original entries from `A_data.json` plus eight additional capability definitions: `P1`, `P2`, `L1`, `K1`, `K2`, `S1`, `P3`, and `D6`. Its current `registry.json` has 37 capability IDs. The ZIP registry has all 37 IDs plus these six:

| ID | Name | Status / evidence date |
|---|---|---|
| `M1` | WhatsApp messaging channel (Cloud API or BSP) | CONFIG; not checked; record carries 2026-10-24 evidence |
| `T1` | Cloud API test environment (test WABA and test number) | CONFIG; checked; 2026-10-24 |
| `C0` | Messaging cost model | CONFIG; checked; 2026-10-24 |
| `X1` | WhatsApp Business Solution Terms constraints | CONFIG; checked; 2026-10-24 |
| `O1` | Messaging policy and opt-in | CONFIG; checked; 2026-10-24 |
| `TP1` | Tech Provider multi-tenant onboarding | CONFIG; checked; 2026-10-24 |

The ZIP also revises records already found in main:

- **B2 — Business Agent:** the ZIP includes retrieved Meta Business Agent documentation and more precise country eligibility, vertical exclusions and pricing evidence. The main generator's older override has secondary-source evidence only and its own different notes.
- **B4 — Darja NLU:** the ZIP retains the local-intent benchmark as OPEN and adds explicit constraints governing the use of WhatsApp Business Solution Data for model training and vendor access.
- **F1 — Business Messaging CAPI:** the ZIP describes the Graph v26.0 endpoint, sender-side deduplication, Status-ad referrals without `ctwa_clid`, and distinguishes the direct `ctwa_clid` route from the hashed-customer-info fallback.
- **F2 — Advanced Matching:** the ZIP specifies the hashed-PII fallback requirements, its seven-day attribution limit and subset-of-countries limitation, and leaves Algeria eligibility OPEN.
- **F3 — Delivery outcome / CAPI:** the ZIP no longer carries the seven-day limit over to the `ctwa_clid` path. It distinguishes documented lifecycle event names from the still-open question of which COD event should be optimized as a purchase.

Therefore the reconciliation is not a simple append of six IDs. Updating only the registry JSON would lose the improvements on the next run of the current `build_registry.py`. The source generator must be changed first, and then the registry must be regenerated.

### Registry integrity (static cross-check only)

A JavaScript cross-check was run against the ZIP's parsed `registry.json`, implementing the current `check.py` rules R1, R2, R3, R5 and R6: allowed status/evidence grades, evidence presence, checked/evidence consistency, dependency reference validity, dependency acyclicity and shape/row references. Result: **0 failures, 14 inherited-READY warnings, no duplicate IDs**.

This was a separately implemented check against the extracted JSON, **not** an execution of the Python `check.py` script and not a substitute for running the repository gate. The 14 warnings identify READY labels inherited from artefact A that have no independent verification.

## Finding F-03 — The bundled full gate cannot run from this ZIP alone (HIGH)

The extracted `gate.py` invokes this sequence:

1. `build_registry.py`
2. `check.py`
3. `build_spec.py`
4. `check_spec.py`
5. `build_plan.py`
6. `plan.py --check`
7. `plan.py --selftest`
8. `python -m unittest discover -s tests -t .`

The `--full` variant also invokes `tests/mutate.py`. The `--verify-results` variant regenerates results and compares them with committed non-empty results files.

The archive contains `build_plan.py` and `plan.py`, but does not contain `build_spec.py`, `check_spec.py`, `core/` or `tests/`. The corresponding `build_spec.py`, `check_spec.py`, `tests/mutate.py` and `system.json` root/expected paths were also not found in GitHub main. As shipped, copying the archive to the repository root cannot make the full gate pass.

The main source generator still defines 37 capabilities, whereas the ZIP registry contains 43. Running the existing builder after copying the ZIP registry into root would regenerate the old 37-record state until the source definitions are reconciled.

## Finding F-04 — Planning data has known unresolved warnings (MEDIUM)

These values were read from the bundled `results_plan.txt`; the plan scripts were **not** executed in this audit:

- Recorded plan check: 0 failures, 4 warnings.
- P5 warnings: `A-03`, `A-10`, and `A-19` have no scenario describing their `fails` outcomes.
- P8 warning: 21 assumptions have no owner.
- Recorded plan self-test: 12/12 expected behaviours.
- Recorded scenario contracts: 21/21 hold.
- Parsed data: 30 roadmap items, 9 scenarios, 21 assumptions (all OPEN and all unowned), 30 documentation entries and 6 HIGH-priority `NOT_READ` items (`N01`–`N06`).

These are saved outputs, not current execution proof. Ownership must not be guessed to silence P8. P5 warnings should be resolved by specifying failure consequences or explicitly justified exceptions—not by weakening the checker.

## Required integration order

1. Preserve the ZIP as a source snapshot. Do not extract its generated files over the active root as a bulk overwrite.
2. Merge the six added capability records and five evidence revisions into the **authored source** used by `build_registry.py`; extend its source URL map and preserve evidence dates per record.
3. Add `build_plan.py`, `plan.py`, `CONTRIBUTING.md`, `AGENTS.md` and the planning source/data in a controlled commit. Regenerate rather than hand-edit `registry.json`, `assumptions.json`, `roadmap.json` and `meta_docs_map.json`.
4. Recover or implement the missing specification/checker/test modules required by `gate.py`. Keep the full gate explicitly blocked until that dependency closure exists.
5. Resolve timestamp semantics: `generated` remains 2026-10-18 in the ZIP even though six new records carry evidence from 2026-10-24. Distinguish build time from evidence-review time without making deterministic result verification flaky.
6. Run `python3 gate.py --full` and then `python3 gate.py --verify-results` in a clean environment. Retain actual logs, exact versions, exit codes and generated artefacts.
7. Merge only after the generator output, source definitions, planning checks, full gate and result-file comparison all agree.

## Evidence classification

- **Directly observed:** latest main upload commit, ZIP blob SHA, exact ten-entry ZIP member list, decompressed sizes and matching CRC-32 values, 43-record parsed registry, source-code blob contents, missing expected root paths, and static JSON invariant-check results.
- **Source-reported but not re-run:** `results_plan.txt` self-tests, scenario contracts and plan warnings.
- **Not run:** Python `build_registry.py`, `check.py`, `build_plan.py`, `plan.py`, `gate.py --full`, `gate.py --verify-results`, unit tests and mutation tests. An attempt to clone GitHub into the tool container failed because that environment could not resolve `github.com`; no Desktop Commander execution device is connected.
- **OPEN:** live Meta account/API eligibility, current Algeria-specific prices and legal conclusions; these require the corresponding primary-source/account/counsel checks listed in the planning data.

## Audit branch

Report branch: `audit/dropbox-reconciliation-2026-10-28`. This branch records findings only; it does not modify `main` or claim production readiness.

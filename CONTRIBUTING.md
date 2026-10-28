# Contributing to Foundation-meta-bus

## Current validation status

The ZIP snapshot in the repository describes a wider full gate, but its executable dependency closure is incomplete: `build_spec.py`, `check_spec.py`, `system.json`, and the core/mutation-test sources were not present in the ZIP and are not currently available at their expected root paths. Do not claim `gate.py --full` or `gate.py --verify-results` passed.

The currently integrated validation sequence is:

```bash
python3 build_registry.py
python3 check.py
python3 build_plan.py
python3 plan.py --check
python3 plan.py --selftest
python3 -m unittest discover -s tests -t .
```

A GitHub Actions workflow runs this sequence and checks that generated files remain reproducible. It is a **registry-and-planning validation gate**, not the missing full production gate.

## Source-of-truth rules

- Edit authored sources: `A_data.json`, `build_registry.py`, `build_plan.py`, `plan.py`, validation code, and tests.
- Regenerate, do not hand-edit, `registry.json`, `claims.json`, `assumptions.json`, `roadmap.json`, and `meta_docs_map.json`.
- Treat `results*.txt` as output artifacts. Do not report a test as run unless its command and result were observed.
- Keep each claim's scope attached to its evidence. Repeated statements do not upgrade an evidence grade.
- Evidence grades are PROVEN, SUPPORTED, OPEN, and CONTRADICTED. Never promote a grade without a new evidence entry, source URL, and retrieval date.
- Unexamined inherited READY labels remain warnings; they are not facts.
- Test fixtures must be synthetic. Do not put real names, phone numbers, credentials, API tokens, customer text, or app secrets in the repository.
- Tests and scripts must not call Meta, couriers, payment providers, LLM APIs, or other external services. Use injected transports and mocks.

## Before merging

1. Review the source diff and the generated-data diff.
2. Run the current validation sequence locally or rely on the corresponding successful GitHub Actions run.
3. Report proven, supported, open and failed items separately.
4. Keep the full gate blocked until the missing spec/check/core/mutation-test files are restored or implemented and the full gate itself passes.
5. Do not change policy rows that require counsel's written decision; tests may exercise overrides, production policy may not.

The original contribution/agent guidance from the Dropbox snapshot is preserved under `docs/reference/dropbox-archive/`.

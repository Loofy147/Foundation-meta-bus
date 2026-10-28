# Foundation-meta-bus

Evidence-backed capability registry and planning foundation for using Meta services (WhatsApp, Marketing API, Conversions API and Business Agent) with businesses operating in Algeria.

## Current contents

- `A_data.json`: source catalogue of the original capability groups.
- `build_registry.py`: builds `registry.json` from the source catalogue, evidence revisions and additional capability definitions.
- `check.py`: validates registry integrity, evidence grades, dependency references, scenario requirements and unsourced numeric claims.
- `build_plan.py` and `plan.py`: build and validate the assumption register, documentation map, roadmap and scenarios.
- `assumptions.json`, `roadmap.json`, `meta_docs_map.json`: generated planning datasets.
- `files - 2026-10-28T093522.822.zip`: preserved Dropbox source snapshot; not a complete extracted source tree.

## Run current validation

```bash
python3 build_registry.py
python3 check.py
python3 build_plan.py
python3 plan.py --check
python3 plan.py --selftest
python3 -m unittest discover -s tests -t .
```

GitHub Actions runs this registry/planning validation and checks generated-file reproducibility. The workflow is **not** the full production gate described in the Dropbox snapshot.

## Known gate limitation

The full gate is not yet executable from the current repository: the expected `build_spec.py`, `check_spec.py`, `system.json`, and full `core/` / mutation-test sources have not been recovered or implemented. Do not claim `gate.py --full` or `gate.py --verify-results` passed.

## Evidence policy

Claims are graded PROVEN, SUPPORTED, OPEN, or CONTRADICTED. A checked capability needs at least one PROVEN or SUPPORTED evidence entry. Inherited READY labels are not verification. Operational availability, pricing, legal eligibility and business outcomes remain OPEN unless the corresponding evidence or experiment is recorded.

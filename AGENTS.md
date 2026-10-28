# Agent guidance

Read `CONTRIBUTING.md` first. The rules here apply in addition to it.

## Ground truth

Use the repository's authored sources and generated outputs. The Dropbox ZIP is a preserved source snapshot; it is not executable source for every component it describes. Do not assume a capability or policy is available because a generated file claims it.

## Required operating loop

1. Inspect the current source and the exact commit being changed.
2. State the evidence and uncertainty for claims that affect design.
3. Make a small, reviewable change in a branch.
4. Regenerate every derived artifact from its authoring source.
5. Run the current registry/planning checks and the unit tests; preserve the real output.
6. Do not mark production ready until the full spec/core gate exists and passes.

## Prohibited shortcuts

- Do not hand-edit generated outputs as the sole fix.
- Do not fabricate sources, test outcomes, implementation status, prices, dates or legal conclusions.
- Do not upgrade a claim from OPEN or SUPPORTED without a new source-backed evidence record.
- Do not send network requests from application scripts or tests.
- Do not store real user data or secrets in fixtures, logs, or commits.
- Do not modify legal/policy decisions that require counsel.
- Do not claim the full gate ran: `build_spec.py`, `check_spec.py`, `system.json`, and core/mutation-test components remain outside the currently verified dependency closure.

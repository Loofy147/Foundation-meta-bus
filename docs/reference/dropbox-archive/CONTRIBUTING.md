# Contributing

This project builds a system that uses Meta services (WhatsApp, Marketing API, Conversions API, Business Agent) for businesses operating in Algeria, alongside other providers. Its rule is simple: nothing is believed because it was written down. Every claim carries a grade, every decision that rests on something unverified is an assumption with a test, and every check is itself tested by breaking things on purpose.

## The one command

```
python3 gate.py            # builds, checks, tests (a few seconds)
python3 gate.py --full     # adds mutation testing of the core (about 80 seconds)
```

A change is not ready until `gate.py --full` passes. Do not describe a check as run unless you ran it and saw the output.

## What you may edit

| Authored (edit these) | Generated (never edit; rebuild) |
|---|---|
| `build_registry.py`, `build_spec.py`, `build_plan.py` | `registry.json`, `claims.json`, `system.json` |
| `core/`, `tests/` | `assumptions.json`, `roadmap.json`, `meta_docs_map.json` |
| `check.py`, `check_spec.py`, `plan.py`, `gen_*.py`, `gate.py` | `results*.txt`, `docs_part*.md` |
| `CONTRIBUTING.md`, `AGENTS.md` | |

## Evidence rules

1. **Four grades only.** PROVEN: a vendor page or paper was retrieved, or a script reproduced it. SUPPORTED: several independent secondary sources agree. OPEN: unverified, one weak source, or sources conflict. CONTRADICTED: evidence found against the claim.
2. **Never upgrade a grade without a new evidence entry.** A secondary source cannot make something PROVEN. A claim proven for one path is not proven for another: the 7-day attribution limit applies to the hashed-identity fallback only, and carrying it over to the `ctwa_clid` path was a mistake that reached a published document.
3. **A capability is `checked=True` only with at least one PROVEN or SUPPORTED entry.** An inherited label from the original artefacts stays a warning until verified.
4. **Cite the final URL and the fetch date.** Meta serves two different versions of the Conversions API guide at an old and a new address (Graph v16.0 and v26.0). A `/preview` terms URL may not be the current version. Record both facts.
5. **Meta changes policy, terms and pricing without notice.** Re-verify pages that a decision rests on; the target cycle is 30 to 90 days (itself assumption A-19).

## Reading Meta documentation

Read the vendor's own pages before building on a service, not after. Add each page to `build_plan.py` under the documentation map with its grade, the facts that matter and the registry ids it affects. A page not read is recorded as NOT_READ with a priority and the assumption it gates, so the gap is visible. Do not write that "all documentation was read".

## Assumptions

Any decision that rests on something unverified becomes an entry in `build_plan.py`: a plain statement, what depends on it, what breaks if it is false, a falsification test, the resources the test needs, and an owner. Every OPEN assumption needs at least one roadmap item that tests it (`plan.py` enforces this). When a test is run, record the result in the assumption's basis, change its status, and add or update the registry evidence. Do not mark an assumption validated because it seems likely.

## Roadmap and scenarios

Items have dependencies and the resources they need. There are no dates and no effort guesses. A scenario is switched on by assumption outcomes (`holds` or `fails`) and changes which items matter. If you add a scenario, add a contract to `CONTRACTS` in `plan.py` stating what must become active or moot; contracts exist because structural checks cannot tell whether a plan makes sense. Ask the plan what to do next:

```
python3 plan.py --have none
python3 plan.py --have none,counsel --done V-04 --assume A-05=fails
```

## Policy decisions belong to counsel

Rows of the policy table in `build_spec.py` are conservative defaults. Only counsel's written ruling may change a decision, and the change must set `decided_on` and `owner`. Tests may override a row to exercise a code path; production code and configuration may not. The shipped policy blocks conversion dispatch on purpose.

## Data and safety

- Fixtures and tests use synthetic data only. No real phone numbers, names, tokens, app secrets or customer text in the repository.
- No test or script sends anything to a network. Transports are injected; the default raises.
- WhatsApp Business Solution Data may not be shared with third parties other than Third Party Service Providers, may not be used to build profiles of individual users beyond message content, and may not train or improve AI models except fine-tuning a model for the business's exclusive use. Models trained on conversation data stay private, datasets derived from conversations are never shared, and no vendor may train on them.
- Do not guess identity. A message without a sender id is rejected, not matched to a nearby contact.

## Tests and mutation

Behaviour gets a unit test. Every guard also gets a mutant in `tests/mutate.py`: a source change that removes the guard, which the suite must catch. A new spec rule gets a mutation in `check_spec.py`; a new plan rule gets one in `plan.py`. A test that cannot fail is not a test: the first plan self-test counted a finding that already existed in the baseline, and was replaced.

## Definition of done

- [ ] `python3 gate.py --full` passes and you read the output
- [ ] New or changed claims have grades and sources with final URLs and dates
- [ ] New unverified dependencies are assumptions with tests and roadmap items
- [ ] New guards have mutants; new scenarios have contracts
- [ ] Generated files were rebuilt, not edited; `results*.txt` come from a real run
- [ ] The change description states what is still unproven

## Recipes

**Add a capability.** Add it to `build_registry.py` with evidence entries. Reference its id from adapters, assumptions or the documentation map.

**Add an adapter.** Register its capabilities first. Add the adapter and the operations it serves in `build_spec.py`; add policy rows for its provider and data classes; wire it into a workflow; run `check_spec.py`. Check that the operation still has an ALLOW path.

**Add a workflow transition.** Declare effects in order, emitted events, and guards. Persist before processing on any transition that captures a referral. Each event has one producing workflow unless declared `multi_producer`.

**Close a roadmap item.** Record the result (assumption basis, registry evidence), rebuild, and run the plan with the item in `--done` to see what it unlocked.

## Change description template

```
What changed:
Evidence and sources (grade, final URL, fetch date):
Assumptions added, tested or changed:
Commands run and their outcome:
Still unproven:
```

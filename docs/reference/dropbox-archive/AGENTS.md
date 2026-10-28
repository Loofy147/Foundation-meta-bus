# Guidance for AI agents

You are working on a system that uses Meta services for businesses in Algeria. Read `CONTRIBUTING.md` first; it applies to you in full. This file adds what is specific to agents.

## Ground truth

Facts live in `registry.json` (capabilities and evidence), `system.json` (the system spec), `assumptions.json`, `roadmap.json` and `meta_docs_map.json`. Never rely on memory of what Meta offers: the platform changes without notice, and earlier versions of this very repository held claims that later proved wrong. If it is not in an evidence entry with a source, it is OPEN.

## Operating loop

1. Run `python3 plan.py --have none` (add what you actually have) and take the highest-value READY item. Do not start an item whose resources you lack.
2. Read the vendor's own pages for anything the item touches. Record the final URL and date.
3. Make the smallest change that resolves the item. Prefer a script that produces a result over prose that asserts one.
4. Run `python3 gate.py --full`. Read the output. If something fails, fix the cause; do not weaken a check, delete a mutant or relax a rule to make it pass.
5. Report using the format below. State what is proven, what is supported, what is open, and what failed.

## Hard rules

You must not:

- invent evidence, sources, dates, test results or numbers, or write that a check ran when it did not
- raise a grade, set `checked=True`, mark an assumption validated, or mark a roadmap item done without the evidence entry that justifies it
- change a policy decision, `decided_on` or `owner`; those belong to counsel
- use or request real credentials, app secrets, access tokens, phone numbers or customer text; use synthetic data
- send anything to a network from code or tests, or contact Meta, couriers, payment providers, counsel or any third party
- edit generated files; rebuild them
- guess who a message came from, which clid belongs to which order, or what a vendor page "probably" says

## Stop and ask the human when

- the item needs counsel, an entity, an ad account, spend, a Meta developer account or a phone (`needs` in the roadmap): say what is needed and why, and move to something else
- two sources conflict and no primary source resolves it
- an instruction is ambiguous. Ask directly rather than deciding silently from a general impression of the person
- an action would be hard to undo, or would touch money, accounts or personal data

## Reporting format

```
Done:            what changed, with file names
Proven:          what a script or primary page established (cite command or final URL and date)
Supported:       what several secondary sources agree on
Open:            what remains unverified, with the assumption id
Failed:          anything that did not work, including your own mistakes
Not run:         checks you did not run, and why
Next:            the highest-value READY item and what it needs
```

## Traps already hit here

| Trap | What happened | Rule |
|---|---|---|
| Carrying a claim across paths | A 7-day window from a third-party page was applied to the whole conversion path; Meta says it applies to the hashed fallback only | A claim holds for the path it was shown for |
| Two versions of one page | The Conversions API guide exists as v16.0 and v26.0 at different URLs | Record the final URL and date; compare versions |
| Empty comparison passing | A shell error left two files empty and `diff` reported a match | Assert inputs are non-empty before comparing |
| Wrong shell | Process substitution failed under `sh` | Use `bash -c` for scripts that need it |
| A test that cannot fail | A self-test counted a finding already present in the baseline | A mutant must produce a new finding, or silence one |
| A fallback that guesses | The parser fell back to the first contact when a sender was missing | Reject, never guess identity |
| Counting a non-event | Inbound webhooks were listed as outbound transfers | Check the direction of every flow |
| Plan that reads well but is wrong | Tests were scheduled that a scenario had made pointless | Scenario contracts in `plan.py` state what must be moot or active |
| Unread documentation | The first design leaned on secondary sources and needed correcting | Read the vendor's pages before building |

## Meta-specific cautions

- WhatsApp Business Solution Data may not train or improve AI models except an exclusive-use fine-tune, may not be shared except with Third Party Service Providers, and may not be used to build profiles of individual users beyond message content. Treat any proposal that moves conversation data to a vendor, a public dataset or a shared model as blocked until counsel rules.
- `ctwa_clid` is per click and is a personal identifier. It is omitted for Status ad placements. Persist it at the first inbound webhook before anything else.
- Meta does not deduplicate business-messaging conversion events. Deduplicate before sending.
- The Business Agent requires the business to be based in an authorized country; do not assume Algeria is one.
- Webhook delivery is retried for up to 7 days, so handlers must be idempotent and return 200 only after a durable write.

#!/usr/bin/env python3
"""
plan.py -- validates and queries the planning layer.

  python3 plan.py --check                         rules only (exit 1 on failure)
  python3 plan.py --have none                     what can start now with no external resources
  python3 plan.py --have none,counsel --done V-01,V-04 --assume A-05=fails,A-01=holds
  python3 plan.py --selftest                      inject faults; every rule must be able to fire

Resources (--have): none dev account spend entity counsel data user. 'none' is always available.
Assumption outcomes (--assume): holds | fails. Outcomes activate scenarios and retire the assumption from the open list.

Rules
  P1 every reference resolves (items, assumptions, registry ids, documentation map)
  P2 the item graph is acyclic
  P3 every OPEN assumption has a falsification test, needed resources, and at least one non-scenario item that tests it
  P4 scenarios reference real assumptions with valid outcomes and state consequences
  P5 (WARN) an assumption with 3 or more dependents has no scenario for its 'fails' outcome
  P6 documentation map: read entries carry url, date and facts; NOT_READ entries carry priority and reason; HIGH ones name the assumptions they gate
  P7 resources named by items and assumptions are from the known set
  P8 (WARN) assumptions without an owner
"""
import json, sys, copy, collections, pathlib, argparse

HERE = pathlib.Path(__file__).parent
def J(name):
    with open(HERE / name, "r", encoding="utf-8") as handle:
        return json.load(handle)
OUTCOMES = ("holds", "fails")

def load():
    return J("registry.json"), J("assumptions.json"), J("roadmap.json"), J("meta_docs_map.json")

def check(reg, ass, road, docs):
    F, W = [], []
    f = lambda r, m: F.append((r, m)); w = lambda r, m: W.append((r, m))
    caps = {c["id"] for c in reg["capabilities"]}
    A = {a["id"]: a for a in ass}; items = {i["id"]: i for i in road["items"]}; scs = {s["id"]: s for s in road["scenarios"]}
    needs_ok = set(road["needs"])
    for a in ass:
        for d in a["depends"]:
            if d not in caps: f("P1", f"assumption {a['id']} depends on unknown registry id {d}")
        for n in a["needs"]:
            if n not in needs_ok: f("P7", f"assumption {a['id']} needs unknown resource {n}")
    tested = collections.defaultdict(list)
    for i in road["items"]:
        for d in i["depends_on"]:
            if d not in items: f("P1", f"item {i['id']} depends on unknown item {d}")
        for t in i["tests"]:
            if t not in A: f("P1", f"item {i['id']} tests unknown assumption {t}")
            elif not i["scenario_only"]: tested[t].append(i["id"])
        for s in i["scenario_only"]:
            if s not in scs: f("P1", f"item {i['id']} is scenario-only for unknown scenario {s}")
        for cond in i["moot_when"]:
            for k, v in cond.items():
                if k not in A or v not in OUTCOMES: f("P1", f"item {i['id']} moot_when {k}={v} invalid")
        for n in i["needs"]:
            if n not in needs_ok: f("P7", f"item {i['id']} needs unknown resource {n}")
    # P2 cycles
    state = {}
    def dfs(n, path):
        if state.get(n) == 1: f("P2", "cycle: " + " -> ".join(path + [n])); return
        if state.get(n) == 2 or n not in items: return
        state[n] = 1
        for d in items[n]["depends_on"]: dfs(d, path + [n])
        state[n] = 2
    for n in items: dfs(n, [])
    # P3 testability
    for a in ass:
        if a["status"] == "OPEN":
            if not a["test"].strip(): f("P3", f"{a['id']} has no falsification test")
            if not a["needs"]: f("P3", f"{a['id']} names no needed resources")
            if not tested.get(a["id"]): f("P3", f"{a['id']} is OPEN but no non-scenario item tests it")
    # P4 scenarios
    for s in road["scenarios"]:
        if not s["when"]: f("P4", f"scenario {s['id']} has no conditions")
        if not s["consequences"]: f("P4", f"scenario {s['id']} states no consequences")
        for k, v in s["when"].items():
            if k not in A: f("P4", f"scenario {s['id']} references unknown assumption {k}")
            if v not in OUTCOMES: f("P4", f"scenario {s['id']} has invalid outcome {v}")
        for k in s["watch"]:
            if k not in A: f("P4", f"scenario {s['id']} watches unknown assumption {k}")
    # P5 coverage
    failing = {k for s in road["scenarios"] for k, v in s["when"].items() if v == "fails"}
    for a in ass:
        if len(a["depends"]) >= 3 and a["id"] not in failing:
            w("P5", f"{a['id']} has {len(a['depends'])} dependents but no scenario for its 'fails' outcome")
    # P6 documentation map
    for d in docs:
        for c in d["affects"]:
            if c not in caps: f("P1", f"doc {d['id']} affects unknown registry id {c}")
        if d["grade"] == "NOT_READ":
            if d.get("priority") not in ("HIGH", "MEDIUM", "LOW") or not d.get("why"): f("P6", f"{d['id']} NOT_READ without priority and reason")
            if d.get("priority") == "HIGH" and not d.get("tests"): f("P6", f"{d['id']} is HIGH but names no gated assumptions")
            for t in d.get("tests", []):
                if t not in A: f("P1", f"doc {d['id']} gates unknown assumption {t}")
        else:
            if not d.get("url") or not d.get("read_on") or not d.get("facts"): f("P6", f"{d['id']} ({d['grade']}) lacks url, date or facts")
    # P8
    unowned = [a["id"] for a in ass if not isinstance(a.get("owner"), str) or not a["owner"].strip()]
    if unowned: w("P8", f"{len(unowned)} assumptions have no owner")
    return F, W

# ------------------------------------------------------------------ what-if
def plan(ass, road, have, done, outcomes):
    A = {a["id"]: a for a in ass}; items = {i["id"]: i for i in road["items"]}
    have = set(have) | {"none"}
    active = [s for s in road["scenarios"] if all(outcomes.get(k) == v for k, v in s["when"].items())]
    active_ids = {s["id"] for s in active}
    dependents = collections.Counter(d for i in road["items"] for d in i["depends_on"])
    status, why = {}, {}
    for i in road["items"]:
        if i["id"] in done: status[i["id"]] = "DONE"; continue
        if i["scenario_only"] and not (set(i["scenario_only"]) & active_ids): status[i["id"]] = "INACTIVE"; continue
        if any(all(outcomes.get(k) == v for k, v in c.items()) for c in i["moot_when"]): status[i["id"]] = "MOOT"; continue
        status[i["id"]] = "?"
    for i in road["items"]:
        if status[i["id"]] != "?": continue
        unmet = [d for d in i["depends_on"] if status.get(d) not in ("DONE", "MOOT")]
        miss = sorted(set(i["needs"]) - have)
        if unmet: status[i["id"]] = "BLOCKED"; why[i["id"]] = "waiting on " + ", ".join(unmet) + (f"; also needs {', '.join(miss)}" if miss else "")
        elif miss: status[i["id"]] = "NEEDS"; why[i["id"]] = "needs " + ", ".join(miss)
        else: status[i["id"]] = "READY"
    def voi(i):
        return sum(len(A[t]["depends"]) for t in i["tests"] if t in A and t not in outcomes) + dependents[i["id"]]
    return active, status, why, voi

def show(ass, road, have, done, outcomes):
    A = {a["id"]: a for a in ass}; items = {i["id"]: i for i in road["items"]}
    active, status, why, voi = plan(ass, road, have, done, outcomes)
    print(f"PLAN  have={sorted(set(have) | {'none'})}  done={sorted(done)}  assume={outcomes}")
    print("Active scenarios: " + ("; ".join(f"{s['id']} {s['title']}" for s in active) or "none (all assumptions still open)"))
    for s in active:
        for c in s["consequences"]: print(f"   - {c}")
    ready = sorted((items[k] for k, v in status.items() if v == "READY"), key=lambda i: (-voi(i), i["id"]))
    print(f"\nREADY now ({len(ready)}), ranked by value of information (assumption dependents plus items unlocked):")
    for i in ready:
        t = [x for x in i["tests"] if x not in outcomes]
        print(f"  {i['id']:5} voi {voi(i):2}  {i['kind']:7} {i['title']}" + (f"  [tests {', '.join(t)}]" if t else ""))
    for label, key in (("NEEDS a resource we lack", "NEEDS"), ("BLOCKED by dependencies", "BLOCKED")):
        rows = [k for k, v in status.items() if v == key]
        if rows:
            print(f"\n{label} ({len(rows)}):")
            for k in rows: print(f"  {k:5} {items[k]['title'][:70]}  ({why[k]})")
    for label, key in (("MOOT in this scenario", "MOOT"), ("INACTIVE scenario-only items", "INACTIVE"), ("DONE", "DONE")):
        rows = [k for k, v in status.items() if v == key]
        if rows: print(f"\n{label}: {', '.join(rows)}")
    openA = [a for a in ass if a["status"] == "OPEN" and a["id"] not in outcomes]
    crit = [a["id"] for a in openA if len(a["depends"]) >= 3]
    print(f"\nOpen assumptions: {len(openA)} of {len(ass)}; load-bearing (3 or more dependents): {', '.join(crit)}")
    nr = [x for x in J("meta_docs_map.json") if x["grade"] == "NOT_READ" and x["priority"] == "HIGH"]
    print(f"Meta documentation not yet read, HIGH priority: {len(nr)}")

# ------------------------------------------------------------------ self-test
def mutations(reg, ass, road, docs):
    def m(name, rule, fn, mode="fires"):
        r, a, ro, d = copy.deepcopy((reg, ass, road, docs)); fn(r, a, ro, d); return name, rule, mode, (r, a, ro, d)
    item = lambda ro, i: next(x for x in ro["items"] if x["id"] == i)
    asm = lambda a, i: next(x for x in a if x["id"] == i)
    return [
     m("item depends on a missing item", "P1", lambda r, a, ro, d: item(ro, "V-01")["depends_on"].append("Z-99")),
     m("assumption depends on a missing registry id", "P1", lambda r, a, ro, d: asm(a, "A-01")["depends"].append("NOPE")),
     m("dependency cycle", "P2", lambda r, a, ro, d: item(ro, "V-04")["depends_on"].append("L-02")),
     m("OPEN assumption nobody tests", "P3", lambda r, a, ro, d: item(ro, "V-01").update(tests=[])),
     m("OPEN assumption with no test text", "P3", lambda r, a, ro, d: asm(a, "A-02").update(test="")),
     m("scenario references a missing assumption", "P4", lambda r, a, ro, d: ro["scenarios"][0]["when"].update({"A-99": "holds"})),
     m("scenario without consequences", "P4", lambda r, a, ro, d: ro["scenarios"][0].update(consequences=[])),
     m("load-bearing assumption loses its failure scenario", "P5", lambda r, a, ro, d: ro.update(scenarios=[s for s in ro["scenarios"] if s["when"].get("A-05") != "fails"])),
     m("primary doc entry without facts", "P6", lambda r, a, ro, d: d[0].update(facts=[])),
     m("HIGH unread doc gates nothing", "P6", lambda r, a, ro, d: next(x for x in d if x["id"] == "N01").update(tests=[])),
     m("unknown resource on an item", "P7", lambda r, a, ro, d: item(ro, "V-01")["needs"].append("wallet")),
     m("assumption loses its accountable owner", "P8", lambda r, a, ro, d: asm(a, "A-01").update(owner=None)),
    ]

# Scenario contracts: expected behaviour of the plan under given outcomes. "active" means not INACTIVE or MOOT or DONE-skipped.
CONTRACTS = [
    ({}, {"SC-2": "INACTIVE", "SC-4": "INACTIVE", "SC-6": "INACTIVE", "SC-7": "INACTIVE", "SC-8": "INACTIVE", "SC-9": "INACTIVE"}),
    ({"A-01": "fails"}, {"X-03": "MOOT", "E-01": "MOOT", "SC-2": "active"}),
    ({"A-05": "fails"}, {"X-03": "MOOT", "E-01": "MOOT", "SC-4": "active"}),
    ({"A-04": "fails"}, {"E-02": "MOOT", "SC-6": "active"}),
    ({"A-08": "fails"}, {"E-02": "MOOT", "SC-9": "active"}),
    ({"A-21": "fails"}, {"SC-7": "active"}),
    ({"A-06": "fails"}, {"SC-8": "active"}),
    ({"A-03": "fails"}, {"X-02": "MOOT", "X-03": "MOOT", "E-01": "MOOT", "SC-10": "active"}),
    ({"A-10": "fails"}, {"E-02": "MOOT", "SC-11": "active"}),
    ({"A-19": "fails"}, {"SC-12": "active"}),
    ({"A-01": "holds", "A-05": "holds", "A-04": "holds"}, {"X-03": "active", "E-02": "active", "E-01": "active"}),
]

def contracts(ass, road):
    out = []
    for outcomes, expect in CONTRACTS:
        _, status, _, _ = plan(ass, road, [], set(), outcomes)
        for item, want in expect.items():
            got = status[item]
            ok = (got not in ("INACTIVE", "MOOT")) if want == "active" else (got == want)
            out.append((f"{outcomes or 'no outcomes'}: {item} should be {want}, is {got}", ok))
    return out

def selftest(reg, ass, road, docs):
    F0, W0 = check(reg, ass, road, docs); base = {m for r, m in F0 + W0}
    res = []
    for name, rule, mode, (r, a, ro, d) in mutations(reg, ass, road, docs):
        F, W = check(r, a, ro, d)
        if mode == "fires":
            ok = any(x == rule and m not in base for x, m in F + W)           # a NEW finding, not one already in the baseline
        else:
            ok = not any(x == rule for x, _ in F + W)
        res.append((name, rule, ok, mode))
    return res

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true"); ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--have", default="none"); ap.add_argument("--done", default=""); ap.add_argument("--assume", default="")
    ns = ap.parse_args()
    reg, ass, road, docs = load()
    F, W = check(reg, ass, road, docs)
    done = {x for x in ns.done.split(",") if x}
    outcomes = dict(p.split("=") for p in ns.assume.split(",") if p)
    for k, v in outcomes.items():
        if k not in {a["id"] for a in ass} or v not in OUTCOMES: sys.exit(f"bad --assume {k}={v}")
    if ns.selftest:
        st = selftest(reg, ass, road, docs)
        for name, rule, ok, mode in st: print(f"  {('caught' if mode == 'fires' else 'silent') if ok else 'MISSED':7} {rule:3} {name}")
        blind = [x for x in st if not x[2]]
        print(f"\nPLAN SELFTEST: {len(st) - len(blind)}/{len(st)} behaved as expected")
        cs = contracts(ass, road); bad = [c for c in cs if not c[1]]
        print("\nSCENARIO CONTRACTS")
        for name, ok in cs: print(f"  {'ok' if ok else 'BROKEN':7} {name}")
        print(f"\nCONTRACTS: {len(cs) - len(bad)}/{len(cs)} hold"); sys.exit(1 if blind or bad else 0)
    if ns.check or not (ns.have != "none" or done or outcomes):
        byr = collections.Counter(r for r, _ in F); byw = collections.Counter(r for r, _ in W)
        print("PLAN CHECK  " + "  ".join(f"P{i}:{byr.get(f'P{i}', 0)}f/{byw.get(f'P{i}', 0)}w" for i in range(1, 9)))
        for r, m_ in F: print(f"  FAIL {r}: {m_}")
        for r, m_ in W: print(f"  warn {r}: {m_}")
        print(f"PLAN: {len(F)} FAIL, {len(W)} warn")
        if ns.check: sys.exit(1 if F else 0)
        print()
    if F: sys.exit("plan has failures; fix before querying")
    show(ass, road, ns.have.split(","), done, outcomes)

if __name__ == "__main__":
    main()

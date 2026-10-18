#!/usr/bin/env python3
"""
check.py -- executes the rules the registry must satisfy and prints a report.
Exit code 1 if any integrity rule fails, so it can gate CI / scheduled re-verification.

Rules
  R1  status in {READY, CONFIG, BLOCKED, UNVERIFIED}; evidence grade in the four allowed grades
  R2  every capability has >=1 evidence entry
  R3  checked=True needs >=1 PROVEN/SUPPORTED evidence entry (otherwise it was not checked)
  R4  (WARNING, not failure) READY without checked=True is a label inherited from A, not a fact
  R5  depends_on ids exist; graph is acyclic
  R6  shape/row requirements and workarounds reference existing ids
"""
import json, sys, pathlib, collections

HERE = pathlib.Path(__file__).parent
R = json.load(open(HERE / "registry.json"))
caps = {c["id"]: c for c in R["capabilities"]}
STAT = ["READY", "CONFIG", "UNVERIFIED", "BLOCKED"]          # severity order
GRADES = set(R["grades"]); STRONG = {"PROVEN", "SUPPORTED"}
fails = []
warns = []
def fail(rule, msg): fails.append(f"{rule}: {msg}")

# ---- integrity ---------------------------------------------------------------
for c in caps.values():
    if c["status"] not in STAT: fail("R1", f"{c['id']} status {c['status']}")
    if not c.get("evidence"): fail("R2", f"{c['id']} has no evidence")
    for e in c.get("evidence", []):
        if e["grade"] not in GRADES: fail("R1", f"{c['id']} grade {e['grade']}")
    if c["checked"] and not any(e["grade"] in STRONG for e in c["evidence"]):
        fail("R3", f"{c['id']} marked checked without PROVEN/SUPPORTED evidence")
    if c["status"] == "READY" and not c["checked"]:
        warns.append(f"R4: {c['id']} READY inherited from A, unverified")
    for d in c["depends_on"]:
        if d not in caps: fail("R5", f"{c['id']} depends on unknown {d}")

# cycle check
state = {}
def dfs(n, path):
    if state.get(n) == 1: fail("R5", "cycle: " + " -> ".join(path + [n])); return
    if state.get(n) == 2: return
    state[n] = 1
    for d in caps[n]["depends_on"]:
        if d in caps: dfs(d, path + [n])
    state[n] = 2
for n in caps: dfs(n, [])

for s in R["shapes"] + R["rows"]:
    for rid in s["requires"]:
        if rid not in caps: fail("R6", f"{s['id']} requires unknown {rid}")
    for a, b in s.get("workarounds", {}).items():
        if a not in caps or b not in caps: fail("R6", f"{s['id']} workaround {a}->{b} unknown")

# ---- effective status with dependency propagation ---------------------------
memo = {}
def eff(n):
    if n in memo: return memo[n]
    worst = STAT.index(caps[n]["status"])
    for d in caps[n]["depends_on"]:
        worst = max(worst, STAT.index(eff(d)))
    memo[n] = STAT[worst]; return memo[n]
for n in caps: eff(n)

def closure(n, seen=None):
    seen = seen if seen is not None else set()
    for d in caps[n]["depends_on"]:
        if d not in seen: seen.add(d); closure(d, seen)
    return seen

print("=" * 72); print("REGISTRY REPORT  generated", R["generated"]); print("=" * 72)

# ---- coverage: nominal vs evidence-backed -----------------------------------
A = [c for c in caps.values() if c["artefact_origin"] == "A"]
nominal_ready = sum(1 for c in A if c["a_status"] == "READY")
print(f"\n[1] COVERAGE (artefact A: {len(A)} capabilities)")
print(f"  A's displayed coverage            : {nominal_ready}/{len(A)} READY = {round(100*nominal_ready/len(A))}%  (computed from its own labels)")
chk = [c for c in A if c["checked"]]
print(f"  examined in this study            : {len(chk)}/{len(A)}")
print(f"  not examined (inherited label)    : {len(A)-len(chk)}/{len(A)}")
changed = [c for c in chk if c["status"] != c["a_status"]]
print(f"  of examined, label changed        : {len(changed)} -> " + ", ".join(f"{c['id']} {c['a_status']}->{c['status']}" for c in changed))
print(f"  of examined, label held           : {len(chk)-len(changed)} -> " + ", ".join(c['id'] for c in chk if c['status']==c['a_status']))
inh_ready = [c["id"] for c in A if c["status"] == "READY" and not c["checked"]]
print(f"  READY labels with NO verification : {len(inh_ready)} -> {', '.join(inh_ready)}")
ver_ready = [c["id"] for c in A if c["status"] == "READY" and c["checked"]]
print(f"  READY labels with verification    : {len(ver_ready)} -> {', '.join(ver_ready) or 'none'}")
added = [c for c in caps.values() if c["artefact_origin"] != "A"]
print(f"  capabilities added (not in A)     : {len(added)} -> " + ", ".join(c["id"] for c in added))

# ---- evidence distribution ---------------------------------------------------
cnt = collections.Counter(e["grade"] for c in caps.values() if c["checked"] for e in c["evidence"])
print(f"\n[2] EVIDENCE ENTRIES on examined items: {dict(cnt)}")
print(f"    primary-source (PROVEN) items      : {sorted({c['id'] for c in caps.values() for e in c['evidence'] if e['grade']=='PROVEN'})}")

# ---- shapes ------------------------------------------------------------------
def open_q(rid):
    """OPEN evidence on an EXAMINED item = a specific unanswered question; inherited OPEN is counted as 'unexamined'."""
    c = caps[rid]
    return [e["claim"] for e in c["evidence"] if e["grade"] == "OPEN"] if c["checked"] else []

def verdict(s):
    blockers, workarounds, gated, unchecked, cfg, openq, replacement_unverified = [], [], [], [], [], [], []
    for rid in s["requires"]:
        st = caps[rid]["status"]
        if st == "BLOCKED":
            alt = s.get("workarounds", {}).get(rid)
            if alt and caps[alt]["status"] not in ("CONFIG", "READY"):
                replacement_unverified.append((rid, alt))
            (workarounds if alt else blockers).append((rid, alt))
        elif st == "UNVERIFIED": gated.append(rid)
        elif st == "CONFIG": cfg.append(rid)
        if not caps[rid]["checked"]: unchecked.append(rid)
        openq += [(rid, q) for q in open_q(rid)]
    n = len(s["requires"])
    if blockers:
        inh = [r for r, _ in blockers if not caps[r]["checked"]]
        v = "BLOCKED AS WRITTEN" + (f" (blocker label INHERITED from A, unverified: {', '.join(inh)})" if inh else " (blocker verified)")
    elif workarounds:
        v = "REDESIGN REQUIRED" + (f" - replacement {', '.join(a for _, a in replacement_unverified)} is itself UNVERIFIED" if replacement_unverified else "")
    elif gated: v = "GATED (unverified dependency)"
    else: v = f"NO KNOWN BLOCKER - but {len(unchecked)}/{n} unexamined, {len(openq)} open question(s)"
    return v, blockers, workarounds, gated, cfg, unchecked, openq

print("\n[3] ARTEFACT B SHAPES vs REGISTRY  (requirement lists are design judgement; see build_registry.py)")
for s in R["shapes"]:
    v, bl, wk, ga, cf, un, oq = verdict(s)
    print(f"\n  Shape {s['id']} '{s['title']}'  ->  {v}")
    print(f"    requires {len(s['requires'])}: {', '.join(s['requires'])}")
    if bl: print(f"    hard blockers        : " + "; ".join(f"{r} ({caps[r]['name']})" for r, _ in bl))
    if wk: print(f"    needs redesign       : " + "; ".join(f"{r} ({caps[r]['name']}) -> use {a} ({caps[a]['name']})" for r, a in wk))
    if ga: print(f"    gated (unverified)   : " + "; ".join(f"{r} ({caps[r]['name']})" for r in ga))
    print(f"    config-dependent     : {', '.join(cf) or '-'}")
    print(f"    deps never examined  : {len(un)}/{len(s['requires'])} -> {', '.join(un)}")
    for r_, q_ in oq: print(f"    OPEN on {r_:3}         : {q_[:100]}")

print("\n[4] ARTEFACT B 'OLD vs NEW' ROWS")
for s in R["rows"]:
    v, bl, wk, ga, cf, un, oq = verdict(s)
    print(f"  {s['id']} {s['title']}\n      -> {v}")

# ---- effective status (propagated) ------------------------------------------
print("\n[5] PROPAGATED STATUS (own status worst-of dependencies) -- examined items only")
for c in caps.values():
    if c["checked"]:
        e = eff(c["id"])
        flag = "" if e == c["status"] else f"  (own {c['status']}, held back by {sorted(d for d in closure(c['id']) if STAT.index(caps[d]['status'])>=STAT.index(e))})"
        print(f"  {c['id']:3} {c['name'][:46]:46} {e:10}{flag}")

# ---- claim ledger -------------------------------------------------------------
LEDGER = [
 # (artefact, claim, kind)  kind: threshold = design parameter to calibrate; outcome = asserted result; display = hardcoded UI value
 ("A", "Adv. Matching lifts match rate +15-25%", "outcome"),
 ("A", "Agents handle 80% of pre-sales in Darja", "outcome"),
 ("A", "Event Match 98.2% (hardcoded in UI, no data source)", "display"),
 ("A", "Hook rate >3s = distribution", "threshold"),
 ("A", ">50 unique asks/week -> validate", "threshold"),
 ("A", "CTR >2.5% and WA conv >8% -> strong", "threshold"),
 ("A", "HOT >15% of flows -> supplier call", "threshold"),
 ("A", "Yalidine rate < 450DA (go criterion)", "threshold"),
 ("A", "Kill in 72h on NO-GO", "threshold"),
 ("A", "Validation cost $35-70 (ads only)", "outcome"),
 ("A", "Next review T+7 days", "threshold"),
 ("B", "ROAS +32%", "outcome"), ("B", "Reply <4s", "outcome"), ("B", "CAC -41%", "outcome"),
 ("B", "COD -68% (returns)", "outcome"), ("B", "Threads +19% reach, DZ <30", "outcome"),
 ("B", "94% of inquiries solved without a human", "outcome"), ("B", "Video completion 2.8x photo", "outcome"),
 ("B", "Return rate 34% -> 11%", "outcome"), ("B", "+240% night conversions", "outcome"),
 ("B", "1 human = 3 stores", "outcome"), ("B", "LTV +2.1x", "outcome"),
 ("B", "Diaspora EUR 38 AOV", "outcome"), ("B", "3M diaspora as TAM", "outcome"),
 ("B", "Owner spends 6h/day replying", "outcome"), ("B", "Ship in 7 days", "threshold"),
]
led = collections.Counter((a, k) for a, _, k in LEDGER)
print("\n[6] CLAIM LEDGER (numeric claims; source links found in either artefact: 0)")
for a in "AB":
    print(f"  {a}: total {sum(v for (x,_),v in led.items() if x==a)} | outcome claims {led[(a,'outcome')]} | design thresholds {led[(a,'threshold')]} | hardcoded display {led[(a,'display')]}")
print("  Handling rule adopted: outcome claims are hypotheses with a measurement plan, never inputs to a decision;")
print("  thresholds are parameters with an owner and a calibration date.")
json.dump([{"artefact": a, "claim": c, "kind": k, "source": None, "status": "UNSOURCED"} for a, c, k in LEDGER],
          open(HERE / "claims.json", "w"), indent=1, ensure_ascii=False)

# ---- verdict -------------------------------------------------------------------
print("\n" + "=" * 72)
if fails:
    print(f"INTEGRITY: {len(fails)} FAILURE(S)"); [print("  -", f) for f in fails]; sys.exit(1)
print(f"INTEGRITY: rules R1,R2,R3,R5,R6 pass | {len(warns)} warning(s): R4 inherited-READY labels with no verification")
print("  " + ", ".join(w.split()[1] for w in warns)); print("=" * 72)

#!/usr/bin/env python3
"""Run the source-level registry, system-spec, planning, unit and mutation gates.

The gate makes no live network calls. --verify-results is strict: each expected
report must exist, be non-empty, and match newly generated output.
"""
import re
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PY = sys.executable
STEPS = [
    ("build registry", ["build_registry.py"]),
    ("check registry", ["check.py"]),
    ("build system specification", ["build_spec.py"]),
    ("check specification and its mutations", ["check_spec.py"]),
    ("build planning data", ["build_plan.py"]),
    ("plan structural checks", ["plan.py", "--check"]),
    ("plan self-tests and scenario contracts", ["plan.py", "--selftest"]),
    ("unit tests", ["-m", "unittest", "discover", "-s", "tests", "-t", "."]),
]
FULL = [("source mutation testing", ["tests/mutate.py"])]
WHATIFS = [
    ["--have", "none"],
    ["--have", "none,counsel", "--done", "V-04", "--assume", "A-05=fails"],
    ["--have", "none,dev,account,spend,entity,counsel,data,user", "--done", "V-01,V-02,V-03,V-04,V-05,V-06,D-01", "--assume", "A-01=fails,A-21=fails,A-04=fails"],
]

def run(args):
    try:
        result = subprocess.run([PY] + args, cwd=HERE, capture_output=True, text=True, timeout=180)
        return result.returncode, result.stdout + result.stderr
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode("utf-8", "replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode("utf-8", "replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        return 124, stdout + stderr + "\nTIMEOUT: command exceeded 180 seconds\n"

def tail(output):
    lines = [line for line in output.strip().splitlines() if line.strip()]
    keep = [line for line in lines if re.search(r"PLAN|SPEC:|SYSTEM SPEC|INTEGRITY|^OK|^Ran|MUTATION|CONTRACTS|killed", line)]
    return (keep or lines or ["(no output)"])[-1][:145]

def required_output(args):
    code, output = run(args)
    if code != 0:
        raise RuntimeError(f"command failed ({code}): {' '.join(args)}\n{output[-5000:]}")
    if not output.strip():
        raise RuntimeError("command produced empty output: " + " ".join(args))
    return output

def generated_results():
    out = {}
    out["results.txt"] = required_output(["check.py"])
    out["results_spec.txt"] = required_output(["check_spec.py"])
    sections = ["== plan rules ==", required_output(["plan.py", "--check"]),
                "== plan self-test and scenario contracts ==", required_output(["plan.py", "--selftest"])]
    for args in WHATIFS:
        sections.extend(["== what-if: plan.py " + " ".join(args) + " ==", required_output(["plan.py"] + args)])
    out["results_plan.txt"] = "\n".join(sections)
    verbose = required_output(["-m", "unittest", "discover", "-s", "tests", "-t", ".", "-v"])
    verbose = "\n".join(line for line in verbose.splitlines() if re.search(r"\.\.\. |^Ran |^OK|^FAILED", line))
    mutation = required_output(["tests/mutate.py"])
    out["results_core.txt"] = "== unittest (verbose) ==\n" + strip_timing(verbose) + "\n\n== mutation ==\n" + mutation
    return out

def strip_timing(value):
    return re.sub(r" in [0-9.]+s", "", value)

def main():
    args = set(sys.argv[1:])
    allowed = {"--full", "--write-results", "--verify-results"}
    unknown = args - allowed
    if unknown:
        raise SystemExit("unknown argument(s): " + ", ".join(sorted(unknown)))
    write = "--write-results" in args
    verify = "--verify-results" in args
    full = "--full" in args or write or verify
    failed = []
    for name, command in STEPS + (FULL if full else []):
        started = time.time()
        code, output = run(command)
        ok = code == 0 and bool(output.strip())
        print(f"  {'PASS' if ok else 'FAIL'}  {name:46} {time.time()-started:5.1f}s  {tail(output)}")
        if not ok:
            failed.append(name)
            if code == 0 and not output.strip(): print("        command returned success but produced no output")
            for line in output.strip().splitlines()[-14:]: print("        " + line)
    if failed:
        print("\nGATE: FAILED (" + ", ".join(failed) + ")")
        raise SystemExit(1)
    if write or verify:
        try:
            outputs = generated_results()
        except Exception as exc:
            print(f"  FAIL  result generation/verification: {type(exc).__name__}: {exc}")
            raise SystemExit(1)
        for filename, content in outputs.items():
            path = HERE / filename
            if not content.strip():
                print(f"  FAIL  {filename}: generated output is empty")
                failed.append(filename)
            elif write:
                path.write_text(content, encoding="utf-8")
                print(f"  wrote {filename} ({len(content.splitlines())} lines)")
            else:
                existing = path.read_text(encoding="utf-8") if path.is_file() else ""
                if not existing.strip():
                    print(f"  FAIL  {filename}: committed report is missing or empty")
                    failed.append(filename)
                    continue
                normalize = lambda value: strip_timing(re.sub(r"docs parts written.*\n?", "", value)).strip()
                matches = normalize(existing) == normalize(content)
                print(f"  {'match' if matches else 'DIFFERS'}  {filename} ({len(content.splitlines())} lines)")
                if not matches: failed.append(filename)
    print("\nGATE: " + ("FAILED (" + ", ".join(failed) + ")" if failed else "PASSED"))
    raise SystemExit(1 if failed else 0)

if __name__ == "__main__": main()

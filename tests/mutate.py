#!/usr/bin/env python3
"""Mutation-test source guards using isolated copies of the actual core and tests."""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
MUTANTS=[
("core/webhook.py","if not verify_signature(payload, signature_header, app_secret):","if False and not verify_signature(payload, signature_header, app_secret):","tests.test_core.WebhookTests.test_bad_signature_is_rejected"),
("core/webhook.py","if not isinstance(sender_id, str) or not sender_id.strip():","if False and (not isinstance(sender_id, str) or not sender_id.strip()):","tests.test_core.WebhookTests.test_missing_sender_is_rejected_without_guessing"),
("core/consent.py","if purpose not in granted:","if False and purpose not in granted:","tests.test_core.PolicyTests.test_marketing_requires_explicit_opt_in"),
("core/policy.py",'if state != "ALLOW":','if False and state != "ALLOW":',"tests.test_core.ConversionTests.test_default_deny_blocks_conversion_dispatch"),
("core/store.py","except sqlite3.IntegrityError:\n                return False","except sqlite3.IntegrityError:\n                return True","tests.test_core.WebhookTests.test_duplicate_webhooks_are_idempotent"),
("core/store.py","if not isinstance(key, str) or not key.strip() or key == identifier:","if not isinstance(key, str) or not key.strip():","tests.test_core.StoreTests.test_plaintext_identifier_index_function_is_rejected"),
("core/webhook.py","if not isinstance(payload, bytes) or len(payload) > MAX_WEBHOOK_BYTES:","if False and (not isinstance(payload, bytes) or len(payload) > MAX_WEBHOOK_BYTES):","tests.test_core.WebhookTests.test_oversized_payload_is_rejected_before_normalization"),
("core/webhook.py",'if not hmac.compare_digest(verify_token.encode("utf-8"), expected_token.encode("utf-8")):','if False and not hmac.compare_digest(verify_token.encode("utf-8"), expected_token.encode("utf-8")):',"tests.test_core.SubscriptionHandshakeTests.test_subscription_handshake_denies_wrong_token_and_mode"),
("core/webhook.py","stored.append(store.put_if_absent(event))","stored.append(store.put_if_absent(events[0]))","tests.test_core.WebhookTests.test_batch_webhook_persists_every_event_and_retry_is_idempotent"),
("core/conversions.py","if not isinstance(clid, str) or not clid.strip():","if False and (not isinstance(clid, str) or not clid.strip()):","tests.test_core.ConversionTests.test_missing_clid_is_rejected"),
]
def execute(cwd,test_name):
    result=subprocess.run([sys.executable,"-m","unittest",test_name],cwd=cwd,capture_output=True,text=True,timeout=30)
    return result.returncode,result.stdout+result.stderr
def kill(path,before,after,test_name):
    baseline,output=execute(ROOT,test_name)
    if baseline!=0: raise RuntimeError("baseline test failed: "+test_name+"\n"+output)
    with tempfile.TemporaryDirectory(prefix="foundation-mutation-") as folder:
        target=Path(folder); shutil.copytree(ROOT/"core",target/"core"); shutil.copytree(ROOT/"tests",target/"tests")
        source=target/path; content=source.read_text(encoding="utf-8")
        if content.count(before)<1: raise RuntimeError("mutation target not found in "+path)
        source.write_text(content.replace(before,after,1),encoding="utf-8")
        mutated,output=execute(target,test_name)
        return mutated!=0, ("" if mutated!=0 else "mutant survived: "+path+" :: "+test_name)
def main():
    failures=[]
    for path,before,after,test_name in MUTANTS:
        try: killed,reason=kill(path,before,after,test_name)
        except Exception as exc: killed,reason=False,f"{path}: {type(exc).__name__}: {exc}"
        print(f"{'KILLED' if killed else 'SURVIVED':8} {path} :: {test_name}")
        if not killed: failures.append(reason)
    print(f"MUTATION: {len(MUTANTS)-len(failures)}/{len(MUTANTS)} killed")
    for failure in failures: print("FAIL:",failure)
    raise SystemExit(1 if failures else 0)
if __name__=="__main__": main()

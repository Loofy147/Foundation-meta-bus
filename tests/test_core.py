import hashlib
import hmac
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from core.consent import authorize_outbound_message
from core.conversions import DispatchOutcomeUnknown, TransportNotConfigured, dispatch_conversion, prepare_conversion
from core.policy import PolicyDenied, authorize
from core.store import SQLiteStore
from core.webhook import InvalidWebhook, PersistenceFailure, MAX_WEBHOOK_BYTES, ingest_signed_payload, verify_subscription

class FakeTransport:
    def __init__(self, error=None): self.calls, self.error = [], error
    def send(self, payload):
        self.calls.append(dict(payload))
        if self.error: raise self.error
        return {"accepted": True}

class CoreTestCase(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tempdir.name) / "foundation-test.sqlite3"
        self.store = SQLiteStore(self.db_path, seal_payload=self.seal, open_payload=self.open_seal, index_identifier=self.index_identifier)
    def tearDown(self):
        self.store.close(); self.tempdir.cleanup()
    @staticmethod
    def index_identifier(namespace, identifier):
        return hmac.new(b"synthetic-index-key", (namespace + "\\0" + identifier).encode("utf-8"), hashlib.sha256).hexdigest()
    @staticmethod
    def seal(raw): return b"SYNTHETIC-TEST-CODEC:" + raw
    @staticmethod
    def open_seal(value):
        prefix = b"SYNTHETIC-TEST-CODEC:"
        if not value.startswith(prefix): raise ValueError("synthetic test codec prefix missing")
        return value[len(prefix):]
    @staticmethod
    def allow_policy():
        return {"state":"ALLOW","owner":"role:test-owner","decided_on":"2026-10-28","evidence":[{"kind":"synthetic-test","ref":"fixture"}]}
    @staticmethod
    def sample_event(): return {"event_id":"evt-synthetic-001","sender_id":"synthetic-sender","referral":{"ctwa_clid":"synthetic-clid"}}
    @staticmethod
    def signed(payload, secret=b"synthetic-secret"):
        return "sha256=" + hmac.new(secret, payload, hashlib.sha256).hexdigest()

class SubscriptionHandshakeTests(CoreTestCase):
    def test_subscription_handshake_returns_original_challenge_for_valid_token(self):
        challenge = "synthetic-challenge-123"
        self.assertEqual(verify_subscription("subscribe", "test-token", "test-token", challenge), challenge)

    def test_subscription_handshake_denies_wrong_token_and_mode(self):
        with self.assertRaises(InvalidWebhook):
            verify_subscription("subscribe", "wrong-token", "test-token", "challenge")
        with self.assertRaises(InvalidWebhook):
            verify_subscription("unsubscribe", "test-token", "test-token", "challenge")
        with self.assertRaises(InvalidWebhook):
            verify_subscription("subscribe", "test-token", "", "challenge")

class PolicyTests(CoreTestCase):
    def test_default_and_approval_required_are_denied(self):
        for policy in (None, {"state":"APPROVAL_REQUIRED"}, {"state":"DENY","owner":"role:test","decided_on":"2026-10-28","evidence":[{"ref":"x"}]}):
            with self.subTest(policy=policy), self.assertRaises(PolicyDenied): authorize(policy)
    def test_allow_requires_owner_date_and_evidence(self):
        with self.assertRaises(PolicyDenied): authorize({"state":"ALLOW","owner":None,"decided_on":None,"evidence":[]})
        self.assertTrue(authorize(self.allow_policy()))
    def test_marketing_requires_explicit_opt_in(self):
        now = datetime.now(timezone.utc)
        common = dict(kind="template",purpose="marketing",now=now,last_inbound_at=now-timedelta(hours=1),policy=self.allow_policy())
        with self.assertRaises(PolicyDenied): authorize_outbound_message(**common,granted_purposes=set())
        self.assertTrue(authorize_outbound_message(**common,granted_purposes={"marketing"}))
    def test_freeform_outside_window_is_rejected(self):
        now = datetime.now(timezone.utc)
        with self.assertRaises(PolicyDenied): authorize_outbound_message(kind="freeform",purpose="service",now=now,last_inbound_at=now-timedelta(hours=25),granted_purposes=set(),policy=self.allow_policy())
    def test_freeform_inside_window_still_needs_policy_allow(self):
        now = datetime.now(timezone.utc)
        self.assertTrue(authorize_outbound_message(kind="freeform",purpose="service",now=now,last_inbound_at=now-timedelta(hours=1),granted_purposes=set(),policy=self.allow_policy()))

class WebhookTests(CoreTestCase):
    def test_valid_signed_event_is_durably_stored_before_ack(self):
        event = self.sample_event(); payload = json.dumps(event,separators=(",",":")).encode()
        receipt = ingest_signed_payload(payload,self.signed(payload),b"synthetic-secret",normalize=lambda d:d,store=self.store)
        self.assertEqual(receipt["status_code"],200); self.assertFalse(receipt["duplicate"])
        self.assertEqual(self.store.get_webhook_event(event["event_id"]),event)
    def test_bad_signature_is_rejected(self):
        payload = json.dumps(self.sample_event()).encode()
        with self.assertRaises(InvalidWebhook): ingest_signed_payload(payload,"sha256=invalid",b"synthetic-secret",normalize=lambda d:d,store=self.store)
        self.assertEqual(self.store.count_webhook_events(),0)
    def test_missing_sender_is_rejected_without_guessing(self):
        payload = json.dumps({"event_id":"evt-no-sender"}).encode()
        with self.assertRaises(InvalidWebhook): ingest_signed_payload(payload,self.signed(payload),b"synthetic-secret",normalize=lambda d:d,store=self.store)
        self.assertIsNone(self.store.get_webhook_event("evt-no-sender"))
    def test_duplicate_webhooks_are_idempotent(self):
        event = self.sample_event(); payload = json.dumps(event,separators=(",",":")).encode()
        first = ingest_signed_payload(payload,self.signed(payload),b"synthetic-secret",normalize=lambda d:d,store=self.store)
        second = ingest_signed_payload(payload,self.signed(payload),b"synthetic-secret",normalize=lambda d:d,store=self.store)
        self.assertFalse(first["duplicate"]); self.assertTrue(second["duplicate"]); self.assertEqual(self.store.count_webhook_events(),1)
    def test_batch_webhook_persists_every_event_and_retry_is_idempotent(self):
        events = [
            {"event_id":"evt-batch-001","sender_id":"synthetic-sender-1"},
            {"event_id":"evt-batch-002","sender_id":"synthetic-sender-2"},
        ]
        payload = b'{"synthetic":"batch"}'
        first = ingest_signed_payload(payload,self.signed(payload),b"synthetic-secret",
            normalize=lambda _document: events,store=self.store)
        retry = ingest_signed_payload(payload,self.signed(payload),b"synthetic-secret",
            normalize=lambda _document: events,store=self.store)
        self.assertEqual(first["events_accepted"],2)
        self.assertEqual(first["duplicates"],0)
        self.assertFalse(first["duplicate"])
        self.assertEqual(retry["duplicates"],2)
        self.assertTrue(retry["duplicate"])
        self.assertEqual(self.store.count_webhook_events(),2)
        self.assertEqual(self.store.get_webhook_event("evt-batch-002"),events[1])

    def test_invalid_event_in_batch_prevents_all_writes(self):
        events = [
            {"event_id":"evt-batch-valid","sender_id":"synthetic-sender"},
            {"event_id":"evt-batch-invalid","sender_id":""},
        ]
        payload = b'{"synthetic":"batch"}'
        with self.assertRaises(InvalidWebhook):
            ingest_signed_payload(payload,self.signed(payload),b"synthetic-secret",
                normalize=lambda _document: events,store=self.store)
        self.assertEqual(self.store.count_webhook_events(),0)

    def test_oversized_payload_is_rejected_before_normalization(self):
        payload = b" " * (MAX_WEBHOOK_BYTES + 1) + b'{"event_id":"evt-large","sender_id":"synthetic-sender"}'
        called = []
        with self.assertRaises(InvalidWebhook):
            ingest_signed_payload(payload,self.signed(payload),b"synthetic-secret",
                normalize=lambda document: called.append(document),store=self.store)
        self.assertEqual(called, [])
        self.assertEqual(self.store.count_webhook_events(), 0)

    def test_storage_failure_prevents_acknowledgement(self):
        payload = json.dumps(self.sample_event()).encode()
        class BrokenStore:
            def put_if_absent(self, _event): raise OSError("synthetic storage failure")
        with self.assertRaises(PersistenceFailure): ingest_signed_payload(payload,self.signed(payload),b"synthetic-secret",normalize=lambda d:d,store=BrokenStore())

class ConversionTests(CoreTestCase):
    def event(self): return {"event_id":"conversion-synthetic-001","event_name":"Purchase","event_time":1793164800,"referral":{"ctwa_clid":"synthetic-clid"},"currency":"DZD","value":1200}
    def test_default_deny_blocks_conversion_dispatch(self):
        policy={"state":"DENY","owner":"role:test-owner","decided_on":"2026-10-28","evidence":[{"kind":"synthetic-test","ref":"fixture"}]}
        transport=FakeTransport()
        with self.assertRaises(PolicyDenied): dispatch_conversion(self.event(),policy,store=self.store,transport=transport)
        self.assertEqual(transport.calls,[]); self.assertIsNone(self.store.get_conversion_status("conversion-synthetic-001"))
    def test_missing_clid_is_rejected(self):
        event=self.event(); del event["referral"]
        with self.assertRaises(ValueError): prepare_conversion(event,self.allow_policy())
    def test_dispatch_once_and_duplicate_is_suppressed(self):
        transport=FakeTransport()
        first=dispatch_conversion(self.event(),self.allow_policy(),store=self.store,transport=transport)
        second=dispatch_conversion(self.event(),self.allow_policy(),store=self.store,transport=transport)
        self.assertEqual(first["status"],"SENT"); self.assertEqual(second["status"],"DUPLICATE")
        self.assertEqual(len(transport.calls),1); self.assertEqual(self.store.get_conversion_status("conversion-synthetic-001"),"SENT")
    def test_ambiguous_send_is_not_automatically_retried(self):
        transport=FakeTransport(TimeoutError("synthetic timeout"))
        with self.assertRaises(DispatchOutcomeUnknown): dispatch_conversion(self.event(),self.allow_policy(),store=self.store,transport=transport)
        self.assertEqual(self.store.get_conversion_status("conversion-synthetic-001"),"UNKNOWN")
        retry=dispatch_conversion(self.event(),self.allow_policy(),store=self.store,transport=transport)
        self.assertEqual(retry["status"],"RECONCILIATION_REQUIRED"); self.assertEqual(len(transport.calls),1)
    def test_transport_is_disabled_without_explicit_injection(self):
        with self.assertRaises(TransportNotConfigured): dispatch_conversion(self.event(),self.allow_policy(),store=self.store)

class StoreTests(CoreTestCase):
    def test_store_requires_an_injected_payload_codec(self):
        with self.assertRaises(ValueError): SQLiteStore(self.db_path,seal_payload=None,open_payload=None,index_identifier=self.index_identifier)
    def test_database_indexes_identifiers_without_storing_raw_ids(self):
        event = self.sample_event()
        self.assertTrue(self.store.put_if_absent(event))
        with self.store._lock:
            columns = {row[1] for row in self.store._db.execute("PRAGMA table_info(webhook_events)")}
            row = self.store._db.execute("SELECT event_key,sender_key FROM webhook_events").fetchone()
        self.assertIn("event_key", columns)
        self.assertIn("sender_key", columns)
        self.assertNotIn("event_id", columns)
        self.assertNotIn("sender_id", columns)
        self.assertNotEqual(row[0], event["event_id"])
        self.assertNotEqual(row[1], event["sender_id"])

    def test_plaintext_identifier_index_function_is_rejected(self):
        weak_path = Path(self.tempdir.name) / "weak-index.sqlite3"
        weak = SQLiteStore(weak_path, seal_payload=self.seal, open_payload=self.open_seal,
                           index_identifier=lambda namespace, identifier: identifier)
        try:
            with self.assertRaises(Exception):
                weak.put_if_absent(self.sample_event())
            self.assertEqual(weak.count_webhook_events(), 0)
        finally:
            weak.close()

    def test_database_persists_sealed_bytes_not_plain_json(self):
        event=self.sample_event(); self.assertTrue(self.store.put_if_absent(event))
        with self.store._lock: stored=self.store._db.execute("SELECT payload FROM webhook_events WHERE event_key=?",(self.index_identifier("event",event["event_id"]),)).fetchone()[0]
        self.assertTrue(bytes(stored).startswith(b"SYNTHETIC-TEST-CODEC:"))
        self.assertNotEqual(bytes(stored),json.dumps(event,ensure_ascii=False,separators=(",",":"),sort_keys=True).encode("utf-8"))

if __name__ == "__main__": unittest.main()

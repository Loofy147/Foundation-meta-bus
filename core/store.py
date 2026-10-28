"""SQLite persistence using sealed payloads and keyed opaque identifier indexes.

Production callers must inject an audited authenticated-encryption codec and a
keyed identifier index (e.g. HMAC with a separately managed key). Test values are
synthetic and are not a production crypto implementation.
"""
import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path


class PersistenceContractError(RuntimeError):
    """Unsafe persistence configuration or invalid state transition."""


class SQLiteStore:
    def __init__(self, path, *, seal_payload, open_payload, index_identifier):
        if not callable(seal_payload) or not callable(open_payload):
            raise ValueError("an injected payload sealing/opening codec is required")
        if not callable(index_identifier):
            raise ValueError("an injected keyed identifier-index function is required")
        self._seal_payload = seal_payload
        self._open_payload = open_payload
        self._index_identifier = index_identifier
        self._lock = threading.RLock()
        self._db = sqlite3.connect(str(Path(path)), isolation_level=None, check_same_thread=False, timeout=5.0)
        self._db.execute("PRAGMA foreign_keys = ON")
        self._db.execute("PRAGMA journal_mode = WAL")
        try:
            self._prepare_schema()
        except Exception:
            self._db.close()
            raise

    def _prepare_schema(self):
        definitions = {
            "webhook_events": (
                "CREATE TABLE webhook_events (event_key TEXT PRIMARY KEY, sender_key TEXT NOT NULL, "
                "payload BLOB NOT NULL, received_at TEXT NOT NULL)"
            ),
            "conversion_outbox": (
                "CREATE TABLE conversion_outbox (event_key TEXT PRIMARY KEY, payload BLOB NOT NULL, "
                "status TEXT NOT NULL CHECK(status IN ('PENDING','SENT','UNKNOWN')), updated_at TEXT NOT NULL)"
            ),
        }
        expected = {
            "webhook_events": {"event_key", "sender_key", "payload", "received_at"},
            "conversion_outbox": {"event_key", "payload", "status", "updated_at"},
        }
        with self._lock:
            for table, columns_required in expected.items():
                exists = self._db.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
                ).fetchone()
                if not exists:
                    self._db.execute(definitions[table])
                    continue
                columns = {row[1] for row in self._db.execute(f"PRAGMA table_info({table})")}
                if not columns_required.issubset(columns) or {"event_id", "sender_id"} & columns:
                    raise PersistenceContractError(
                        f"legacy or incompatible schema in {table}; migrate or securely retire it explicitly"
                    )

    def _identifier_key(self, namespace, identifier):
        if not isinstance(identifier, str) or not identifier.strip():
            raise ValueError(f"{namespace} identifier is required")
        key = self._index_identifier(namespace, identifier)
        if not isinstance(key, str) or not key.strip() or key == identifier:
            raise PersistenceContractError(
                "identifier index must return a non-empty opaque keyed value, not the raw identifier"
            )
        return key

    def _sealed_json(self, value):
        raw = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
        sealed = self._seal_payload(raw)
        if not isinstance(sealed, bytes) or not sealed or sealed == raw:
            raise PersistenceContractError("payload codec must return non-empty sealed bytes, not plaintext")
        return sealed

    def put_if_absent(self, event):
        if not isinstance(event, dict):
            raise ValueError("canonical event must be a mapping")
        event_id, sender_id = event.get("event_id"), event.get("sender_id")
        event_key = self._identifier_key("event", event_id)
        sender_key = self._identifier_key("sender", sender_id)
        payload = self._sealed_json(event)
        with self._lock:
            try:
                cursor = self._db.execute(
                    "INSERT INTO webhook_events(event_key,sender_key,payload,received_at) VALUES(?,?,?,?)",
                    (event_key, sender_key, sqlite3.Binary(payload), datetime.now(timezone.utc).isoformat()),
                )
            except sqlite3.IntegrityError:
                return False
        return cursor.rowcount == 1

    def get_webhook_event(self, event_id):
        event_key = self._identifier_key("event", event_id)
        with self._lock:
            row = self._db.execute("SELECT payload FROM webhook_events WHERE event_key=?", (event_key,)).fetchone()
        if row is None:
            return None
        raw = self._open_payload(bytes(row[0]))
        if not isinstance(raw, bytes):
            raise PersistenceContractError("payload opening codec must return bytes")
        return json.loads(raw.decode("utf-8"))

    def count_webhook_events(self):
        with self._lock:
            return self._db.execute("SELECT COUNT(*) FROM webhook_events").fetchone()[0]

    def reserve_conversion(self, event_id, payload):
        event_key = self._identifier_key("event", event_id)
        sealed = self._sealed_json(payload)
        with self._lock:
            try:
                cursor = self._db.execute(
                    "INSERT INTO conversion_outbox(event_key,payload,status,updated_at) VALUES(?,?,?,?)",
                    (event_key, sqlite3.Binary(sealed), "PENDING", datetime.now(timezone.utc).isoformat()),
                )
            except sqlite3.IntegrityError:
                return False
        return cursor.rowcount == 1

    def mark_conversion_outcome(self, event_id, outcome):
        if outcome not in {"SENT", "UNKNOWN"}:
            raise ValueError("outcome must be SENT or UNKNOWN")
        event_key = self._identifier_key("event", event_id)
        with self._lock:
            cursor = self._db.execute(
                "UPDATE conversion_outbox SET status=?,updated_at=? WHERE event_key=? AND status='PENDING'",
                (outcome, datetime.now(timezone.utc).isoformat(), event_key),
            )
        if cursor.rowcount != 1:
            raise PersistenceContractError("outbox transition missing or not from PENDING")

    def get_conversion_status(self, event_id):
        event_key = self._identifier_key("event", event_id)
        with self._lock:
            row = self._db.execute("SELECT status FROM conversion_outbox WHERE event_key=?", (event_key,)).fetchone()
        return None if row is None else row[0]

    def close(self):
        with self._lock:
            self._db.close()

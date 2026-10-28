"""SQLite persistence with injected payload sealing/opening callbacks.

The test codec is deliberately synthetic and is not cryptographic. Production callers
must supply an audited authenticated-encryption codec and key-management lifecycle.
"""
import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path

class PersistenceContractError(RuntimeError):
    """Raised for invalid persistence state transitions or a weak codec contract."""

class SQLiteStore:
    def __init__(self, path, *, seal_payload, open_payload):
        if not callable(seal_payload) or not callable(open_payload):
            raise ValueError("an injected payload sealing/opening codec is required")
        self._seal_payload = seal_payload
        self._open_payload = open_payload
        self._lock = threading.RLock()
        self._db = sqlite3.connect(str(Path(path)), isolation_level=None, check_same_thread=False, timeout=5.0)
        self._db.execute("PRAGMA foreign_keys = ON")
        self._db.execute("PRAGMA journal_mode = WAL")
        self._db.execute("CREATE TABLE IF NOT EXISTS webhook_events (event_id TEXT PRIMARY KEY, sender_id TEXT NOT NULL, payload BLOB NOT NULL, received_at TEXT NOT NULL)")
        self._db.execute("CREATE TABLE IF NOT EXISTS conversion_outbox (event_id TEXT PRIMARY KEY, payload BLOB NOT NULL, status TEXT NOT NULL CHECK(status IN ('PENDING','SENT','UNKNOWN')), updated_at TEXT NOT NULL)")

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
        if not isinstance(event_id, str) or not event_id.strip():
            raise ValueError("event_id is required")
        if not isinstance(sender_id, str) or not sender_id.strip():
            raise ValueError("sender_id is required")
        payload = self._sealed_json(event)
        with self._lock:
            try:
                cursor = self._db.execute("INSERT INTO webhook_events(event_id,sender_id,payload,received_at) VALUES(?,?,?,?)",
                    (event_id, sender_id, sqlite3.Binary(payload), datetime.now(timezone.utc).isoformat()))
            except sqlite3.IntegrityError:
                return False
        return cursor.rowcount == 1

    def get_webhook_event(self, event_id):
        with self._lock:
            row = self._db.execute("SELECT payload FROM webhook_events WHERE event_id=?", (event_id,)).fetchone()
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
        if not isinstance(event_id, str) or not event_id.strip():
            raise ValueError("stable event_id is required")
        sealed = self._sealed_json(payload)
        with self._lock:
            try:
                cursor = self._db.execute("INSERT INTO conversion_outbox(event_id,payload,status,updated_at) VALUES(?,?,?,?)",
                    (event_id, sqlite3.Binary(sealed), "PENDING", datetime.now(timezone.utc).isoformat()))
            except sqlite3.IntegrityError:
                return False
        return cursor.rowcount == 1

    def mark_conversion_outcome(self, event_id, outcome):
        if outcome not in {"SENT", "UNKNOWN"}:
            raise ValueError("outcome must be SENT or UNKNOWN")
        with self._lock:
            cursor = self._db.execute("UPDATE conversion_outbox SET status=?,updated_at=? WHERE event_id=? AND status='PENDING'",
                (outcome, datetime.now(timezone.utc).isoformat(), event_id))
        if cursor.rowcount != 1:
            raise PersistenceContractError("outbox transition missing or not from PENDING")

    def get_conversion_status(self, event_id):
        with self._lock:
            row = self._db.execute("SELECT status FROM conversion_outbox WHERE event_id=?", (event_id,)).fetchone()
        return None if row is None else row[0]

    def close(self):
        with self._lock:
            self._db.close()

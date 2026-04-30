"""Persistence helpers for Toma.

The item catalog remains in a local SQLite database. Medication log entries are
stored in Firmament (Supabase/Postgres) when ``SUPABASE_URL`` and
``SUPABASE_ANON_KEY`` are configured, with SQLite available for tests and local
fallbacks.
"""

from __future__ import annotations

import json
import os
import sqlite3
import urllib.error
import urllib.parse
import urllib.request
from contextlib import contextmanager
from datetime import UTC, datetime, time
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).parent / "toma.db"
MEDICATION_LOGS_TABLE = "medication_logs"
_SUPABASE_CLIENT: "SupabaseMedicationLogClient | None" = None
_SUPABASE_ENABLED_OVERRIDE: bool | None = None


@contextmanager
def get_connection():
    """Connect to SQLite database with WAL mode and foreign keys enabled."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Create local SQLite tables and indexes if they don't exist."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                category TEXT NOT NULL DEFAULT 'supplement',
                default_dosage REAL,
                dosage_unit TEXT NOT NULL DEFAULT 'mg',
                description TEXT NOT NULL DEFAULT '',
                notes TEXT NOT NULL DEFAULT '',
                sort_order INTEGER NOT NULL DEFAULT 0,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_items_category ON items(category)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_items_is_active ON items(is_active)
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS daily_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                log_date TEXT NOT NULL,
                item_id INTEGER NOT NULL,
                dosage_taken REAL,
                notes TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (item_id) REFERENCES items(id),
                UNIQUE(log_date, item_id)
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_daily_logs_date ON daily_logs(log_date)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_daily_logs_item ON daily_logs(item_id)
        """)


def configure_supabase_client(client: "SupabaseMedicationLogClient | None") -> None:
    """Override the medication log client, primarily for tests."""
    global _SUPABASE_CLIENT
    _SUPABASE_CLIENT = client


def configure_supabase_enabled(enabled: bool | None) -> None:
    """Override whether medication logs use Supabase.

    ``None`` restores environment-based detection.
    """
    global _SUPABASE_ENABLED_OVERRIDE
    _SUPABASE_ENABLED_OVERRIDE = enabled


def is_supabase_enabled() -> bool:
    """Return whether medication logs should use Supabase as primary storage."""
    if _SUPABASE_ENABLED_OVERRIDE is not None:
        return _SUPABASE_ENABLED_OVERRIDE
    return bool(os.environ.get("SUPABASE_URL") and os.environ.get("SUPABASE_ANON_KEY"))


def get_supabase_client() -> "SupabaseMedicationLogClient":
    """Return the configured Firmament medication log client."""
    global _SUPABASE_CLIENT
    if _SUPABASE_CLIENT is None:
        _SUPABASE_CLIENT = SupabaseMedicationLogClient.from_env()
    return _SUPABASE_CLIENT


def log_date_to_timestamp(log_date: str) -> str:
    """Convert a YYYY-MM-DD log date to the canonical Supabase timestamp."""
    dt = datetime.combine(datetime.fromisoformat(log_date).date(), time.min, tzinfo=UTC)
    return dt.isoformat().replace("+00:00", "Z")


class SupabaseMedicationLogClient:
    """Tiny PostgREST client for Firmament medication log storage."""

    def __init__(self, url: str, anon_key: str, table: str = MEDICATION_LOGS_TABLE):
        self.url = url.rstrip("/")
        self.anon_key = anon_key
        self.table = table
        self.endpoint = f"{self.url}/rest/v1/{self.table}"

    @classmethod
    def from_env(cls) -> "SupabaseMedicationLogClient":
        """Build a client from the personal-mcp SUPABASE_* environment pattern."""
        url = os.environ.get("SUPABASE_URL")
        anon_key = os.environ.get("SUPABASE_ANON_KEY")
        if not url or not anon_key:
            raise RuntimeError(
                "SUPABASE_URL and SUPABASE_ANON_KEY are required for medication logs"
            )
        return cls(url, anon_key)

    def upsert_log(
        self,
        *,
        timestamp: str,
        name: str,
        dose: float | None,
        unit: str,
        notes: str,
        category: str,
    ) -> None:
        """Insert or update one medication log row."""
        payload = {
            "timestamp": timestamp,
            "name": name,
            "dose": dose,
            "unit": unit or "",
            "notes": notes or "",
            "category": category or "supplement",
        }
        self._request(
            "POST",
            params={"on_conflict": "timestamp,name"},
            headers={"Prefer": "resolution=merge-duplicates,return=minimal"},
            body=[payload],
        )

    def list_logs(
        self, *, start_timestamp: str, end_timestamp: str
    ) -> list[dict[str, Any]]:
        """Return medication log rows in timestamp order for an inclusive range."""
        return self._request(
            "GET",
            params={
                "select": "timestamp,name,dose,unit,notes,category",
                "timestamp": [f"gte.{start_timestamp}", f"lte.{end_timestamp}"],
                "order": "timestamp.asc,name.asc",
            },
        )

    def _request(
        self,
        method: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        body: Any | None = None,
    ) -> Any:
        query = _encode_postgrest_params(params or {})
        url = f"{self.endpoint}?{query}" if query else self.endpoint
        request_headers = {
            "apikey": self.anon_key,
            "Authorization": f"Bearer {self.anon_key}",
            "Accept": "application/json",
        }
        if body is not None:
            request_headers["Content-Type"] = "application/json"
        if headers:
            request_headers.update(headers)

        data = json.dumps(body).encode("utf-8") if body is not None else None
        req = urllib.request.Request(
            url, data=data, headers=request_headers, method=method
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                raw = resp.read()
                if not raw:
                    return None
                return json.loads(raw)
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"Supabase {method} {self.table} failed: {detail}"
            ) from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise RuntimeError(
                f"Supabase {method} {self.table} request to {url} failed: {exc}"
            ) from exc


def _encode_postgrest_params(params: dict[str, Any]) -> str:
    pairs: list[tuple[str, str]] = []
    for key, value in params.items():
        if isinstance(value, list):
            pairs.extend((key, str(item)) for item in value)
        else:
            pairs.append((key, str(value)))
    return urllib.parse.urlencode(pairs)

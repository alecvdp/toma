"""Daily log CRUD operations and grid building."""

from __future__ import annotations

from datetime import UTC, datetime, time
from typing import Any

import pandas as pd

from db import (
    get_connection,
    get_supabase_client,
    is_supabase_enabled,
    log_date_to_timestamp,
)


def upsert_log_entry(
    log_date: str,
    item_id: int,
    dosage_taken: float | None,
    notes: str = "",
) -> None:
    """Insert or update a log entry for (log_date, item_id)."""
    if is_supabase_enabled():
        item = _get_item(item_id)
        if item is None:
            raise ValueError(f"Unknown item_id: {item_id}")
        get_supabase_client().upsert_log(
            timestamp=log_date_to_timestamp(log_date),
            name=item["name"],
            dose=dosage_taken,
            unit=item.get("dosage_unit") or "",
            notes=notes,
            category=item.get("category") or "supplement",
        )
        return

    with get_connection() as conn:
        conn.execute(
            """INSERT INTO daily_logs (log_date, item_id, dosage_taken, notes)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(log_date, item_id) DO UPDATE SET
                   dosage_taken = excluded.dosage_taken,
                   notes = excluded.notes,
                   updated_at = datetime('now')""",
            (log_date, item_id, dosage_taken, notes),
        )


def take_all_fixed_dose(log_date: str) -> int:
    """Insert default dosages for all active fixed-dose items not yet logged.

    Returns the number of rows inserted.
    """
    if is_supabase_enabled():
        items = _get_active_items_ordered()
        existing_names = {
            row["item_name"] for row in get_logs_by_date(log_date)
        }
        inserted = 0
        for item in items:
            if item.get("default_dosage") is None or item["name"] in existing_names:
                continue
            upsert_log_entry(log_date, item["id"], item["default_dosage"])
            inserted += 1
        return inserted

    with get_connection() as conn:
        cursor = conn.execute(
            """INSERT OR IGNORE INTO daily_logs (log_date, item_id, dosage_taken)
               SELECT ?, id, default_dosage
               FROM items
               WHERE is_active = 1
                 AND default_dosage IS NOT NULL
                 AND id NOT IN (
                     SELECT item_id FROM daily_logs WHERE log_date = ?
                 )""",
            (log_date, log_date),
        )
        return cursor.rowcount


def get_logs_by_date(log_date: str) -> list[dict]:
    """Get all log entries for a date, joined with item info.

    Returns list of dicts with keys: item_id, item_name, dosage_taken,
    notes, default_dosage, dosage_unit.
    """
    if is_supabase_enabled():
        items_by_name = {item["name"]: item for item in _get_active_items_ordered()}
        rows = _supabase_logs_for_date_range(log_date, log_date)
        entries = []
        for row in rows:
            item = items_by_name.get(row.get("name"))
            if item is None:
                continue
            entries.append(
                {
                    "item_id": item["id"],
                    "item_name": item["name"],
                    "dosage_taken": row.get("dose"),
                    "notes": row.get("notes") or "",
                    "default_dosage": item.get("default_dosage"),
                    "dosage_unit": row.get("unit") or item.get("dosage_unit"),
                }
            )
        return sorted(entries, key=lambda e: (_sort_value(items_by_name[e["item_name"]]), e["item_name"]))

    with get_connection() as conn:
        rows = conn.execute(
            """SELECT
                   dl.item_id,
                   i.name AS item_name,
                   dl.dosage_taken,
                   dl.notes,
                   i.default_dosage,
                   i.dosage_unit
               FROM daily_logs dl
               JOIN items i ON dl.item_id = i.id
               WHERE dl.log_date = ?
                 AND i.is_active = 1
               ORDER BY i.sort_order, i.name""",
            (log_date,),
        ).fetchall()
        return [dict(r) for r in rows]


def build_log_grid(target_date: str) -> pd.DataFrame:
    """Build a single-row DataFrame with item names as columns.

    All active items appear as columns (ordered by sort_order, name).
    Items with no log entry for the target_date get NaN.
    """
    if is_supabase_enabled():
        items = _get_active_items_ordered()
        values = {entry["item_name"]: entry["dosage_taken"] for entry in get_logs_by_date(target_date)}
        data = {item["name"]: values.get(item["name"]) for item in items}
        return pd.DataFrame([data], index=[target_date])

    with get_connection() as conn:
        rows = conn.execute(
            """SELECT
                   i.name AS item_name,
                   dl.dosage_taken
               FROM items i
               LEFT JOIN daily_logs dl
                   ON dl.item_id = i.id AND dl.log_date = ?
               WHERE i.is_active = 1
               ORDER BY i.sort_order, i.name""",
            (target_date,),
        ).fetchall()

    data = {row["item_name"]: row["dosage_taken"] for row in rows}
    df = pd.DataFrame([data], index=[target_date])
    return df


def get_logs_by_date_range(start_date: str, end_date: str) -> pd.DataFrame:
    """Return a DataFrame with dates as rows and active items as columns.

    Dates with no log entries at all are excluded (only dates with at least
    one entry appear). Items with no entry for a given date show NaN.
    """
    if is_supabase_enabled():
        return _supabase_logs_to_dataframe(start_date, end_date)

    with get_connection() as conn:
        rows = conn.execute(
            """SELECT
                   dl.log_date,
                   i.name AS item_name,
                   dl.dosage_taken,
                   i.sort_order
               FROM daily_logs dl
               JOIN items i ON dl.item_id = i.id
               WHERE dl.log_date BETWEEN ? AND ?
                 AND i.is_active = 1
               ORDER BY dl.log_date, i.sort_order, i.name""",
            (start_date, end_date),
        ).fetchall()

    if not rows:
        return pd.DataFrame()

    data = [dict(r) for r in rows]
    return _logs_to_pivot(data)


def export_logs_csv(df: pd.DataFrame) -> bytes:
    """Export a DataFrame to UTF-8 encoded CSV bytes.

    The index column is labeled 'date'. This keeps CSV available as an export
    format while Supabase is the primary medication-log store.
    """
    df = df.copy()
    if df.index.name != "date":
        df.index.name = "date"
    return df.to_csv().encode("utf-8")


def _get_item(item_id: int) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
    return dict(row) if row else None


def _get_active_items_ordered() -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM items WHERE is_active = 1 ORDER BY sort_order, name"
        ).fetchall()
    return [dict(r) for r in rows]


def _supabase_logs_for_date_range(start_date: str, end_date: str) -> list[dict[str, Any]]:
    return get_supabase_client().list_logs(
        start_timestamp=log_date_to_timestamp(start_date),
        end_timestamp=_end_of_day_timestamp(end_date),
    )


def _supabase_logs_to_dataframe(start_date: str, end_date: str) -> pd.DataFrame:
    items_by_name = {item["name"]: item for item in _get_active_items_ordered()}
    rows = []
    for row in _supabase_logs_for_date_range(start_date, end_date):
        item = items_by_name.get(row.get("name"))
        if item is None:
            continue
        rows.append(
            {
                "log_date": _timestamp_to_date(row["timestamp"]),
                "item_name": item["name"],
                "dosage_taken": row.get("dose"),
                "sort_order": item.get("sort_order") or 0,
            }
        )

    if not rows:
        return pd.DataFrame()
    return _logs_to_pivot(rows)


def _logs_to_pivot(data: list[dict[str, Any]]) -> pd.DataFrame:
    df = pd.DataFrame(data)
    pivot = df.pivot_table(
        index="log_date",
        columns="item_name",
        values="dosage_taken",
        aggfunc="first",
    )
    pivot.index.name = "date"
    pivot = pivot.sort_index()

    col_order_map = {}
    for row in data:
        if row["item_name"] not in col_order_map:
            col_order_map[row["item_name"]] = (row["sort_order"], row["item_name"])
    ordered_cols = sorted(pivot.columns, key=lambda c: col_order_map.get(c, (0, c)))
    return pivot[ordered_cols]


def _end_of_day_timestamp(log_date: str) -> str:
    dt = datetime.combine(datetime.fromisoformat(log_date).date(), time.max, tzinfo=UTC)
    return dt.isoformat().replace("+00:00", "Z")


def _timestamp_to_date(timestamp: str) -> str:
    normalized = timestamp.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized).date().isoformat()


def _sort_value(item: dict[str, Any]) -> int:
    return item.get("sort_order") or 0

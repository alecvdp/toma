"""Daily log CRUD operations and grid building."""

import pandas as pd

from db import get_connection


def upsert_log_entry(
    log_date: str,
    item_id: int,
    dosage_taken: float | None,
    notes: str = "",
) -> None:
    """Insert or update a log entry for (log_date, item_id)."""
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

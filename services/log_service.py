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


def get_logs_by_date_range(start_date: str, end_date: str) -> pd.DataFrame:
    """Return a DataFrame with dates as rows and active items as columns.

    Dates with no log entries at all are excluded (only dates with at least
    one entry appear). Items with no entry for a given date show NaN.
    """
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
    df = pd.DataFrame(data)
    pivot = df.pivot_table(
        index="log_date",
        columns="item_name",
        values="dosage_taken",
        aggfunc="first",
    )
    pivot.index.name = "date"
    pivot = pivot.sort_index()

    # Order columns by sort_order then name
    col_order_map = {}
    for r in data:
        if r["item_name"] not in col_order_map:
            col_order_map[r["item_name"]] = (r["sort_order"], r["item_name"])
    ordered_cols = sorted(pivot.columns, key=lambda c: col_order_map.get(c, (0, c)))
    pivot = pivot[ordered_cols]

    return pivot


def export_logs_csv(df: pd.DataFrame) -> bytes:
    """Export a DataFrame to UTF-8 encoded CSV bytes.

    The index column is labeled 'date'.
    """
    df = df.copy()
    if df.index.name != "date":
        df.index.name = "date"
    return df.to_csv().encode("utf-8")

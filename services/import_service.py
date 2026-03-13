"""Import validation and data loading for CSV/Excel files."""

import re

import pandas as pd

from services.log_service import upsert_log_entry


def _parse_numeric(value) -> float | None:
    """Extract numeric value from strings like '750mg', '2.5 tablets'."""
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip()
    match = re.match(r"^([0-9]*\.?[0-9]+)", s)
    return float(match.group(1)) if match else None


def validate_import(
    df: pd.DataFrame, active_items: list[dict]
) -> tuple[bool, list[str]]:
    """Validate an import DataFrame against the active item catalog.

    Returns (is_valid, messages) where messages contains errors or warnings.
    """
    messages: list[str] = []

    # Normalize column names (case-insensitive, strip whitespace)
    df.columns = df.columns.str.strip().str.lower()

    # Check for required 'date' column
    if "date" not in df.columns:
        messages.append("Missing required 'date' column")
        return False, messages

    # Get item column names (everything except 'date')
    item_columns = [c for c in df.columns if c != "date"]
    item_name_lower = {item["name"].lower(): item["name"] for item in active_items}

    matched = [c for c in item_columns if c in item_name_lower]
    unrecognized = [c for c in item_columns if c not in item_name_lower]

    if unrecognized:
        messages.append(
            f"Unrecognized columns (will be skipped): {', '.join(unrecognized)}"
        )

    if not matched:
        messages.append("No columns match any active catalog items")
        return False, messages

    return True, messages


def import_logs(df: pd.DataFrame, active_items: list[dict]) -> int:
    """Import log entries from a DataFrame.

    For each row, extracts the date and upserts entries for columns
    that match active item names. Returns count of entries imported.
    """
    # Normalize column names to match validation
    df.columns = df.columns.str.strip().str.lower()

    item_name_lower = {item["name"].lower(): item["id"] for item in active_items}
    item_columns = [c for c in df.columns if c != "date" and c in item_name_lower]

    count = 0
    for _, row in df.iterrows():
        log_date = str(row["date"])
        for col in item_columns:
            value = row[col]
            # Skip NaN values
            if pd.isna(value):
                continue
            numeric = _parse_numeric(value)
            if numeric is None:
                continue
            item_id = item_name_lower[col]
            upsert_log_entry(log_date, item_id, numeric)
            count += 1

    return count

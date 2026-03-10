"""Import validation and data loading for CSV/Excel files."""

import math

import pandas as pd

from services.log_service import upsert_log_entry


def validate_import(
    df: pd.DataFrame, active_items: list[dict]
) -> tuple[bool, list[str]]:
    """Validate an import DataFrame against the active item catalog.

    Returns (is_valid, messages) where messages contains errors or warnings.
    """
    messages: list[str] = []

    # Check for required 'date' column
    if "date" not in df.columns:
        messages.append("Missing required 'date' column")
        return False, messages

    # Get item column names (everything except 'date')
    item_columns = [c for c in df.columns if c != "date"]
    active_item_names = {item["name"] for item in active_items}

    matched = [c for c in item_columns if c in active_item_names]
    unrecognized = [c for c in item_columns if c not in active_item_names]

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
    item_name_to_id = {item["name"]: item["id"] for item in active_items}
    item_columns = [c for c in df.columns if c != "date" and c in item_name_to_id]

    count = 0
    for _, row in df.iterrows():
        log_date = str(row["date"])
        for col in item_columns:
            value = row[col]
            # Skip NaN values
            if pd.isna(value):
                continue
            item_id = item_name_to_id[col]
            upsert_log_entry(log_date, item_id, float(value))
            count += 1

    return count

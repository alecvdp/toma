#!/usr/bin/env python3
"""Seed Firmament medication_logs from a legacy manual_log.csv export.

Expected CSV shape matches Toma exports: a ``date`` column plus one column per
catalog item. Configure ``SUPABASE_URL`` and ``SUPABASE_ANON_KEY`` before
running. By default this reads ``manual_log.csv`` from the repository root.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

import db
from services.import_service import import_logs, validate_import
from services.item_service import get_active_items


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Migrate legacy manual_log.csv data into Firmament medication_logs."
    )
    parser.add_argument(
        "csv_path",
        nargs="?",
        default="manual_log.csv",
        help="Path to the legacy CSV export (default: manual_log.csv).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    csv_path = Path(args.csv_path)
    if not csv_path.exists():
        raise SystemExit(f"CSV file not found: {csv_path}")

    db.init_db()
    db.configure_supabase_enabled(True)

    active_items = get_active_items()
    if not active_items:
        raise SystemExit("No active catalog items found. Seed the item catalog first.")

    df = pd.read_csv(csv_path)
    is_valid, messages = validate_import(df, active_items)
    for message in messages:
        print(message)
    if not is_valid:
        raise SystemExit("CSV validation failed; no rows migrated.")

    count = import_logs(df, active_items)
    print(f"Migrated {count} medication log entries to Supabase.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

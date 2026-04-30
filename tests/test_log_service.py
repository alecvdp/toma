"""Tests for daily log service functions."""

import pandas as pd

import db
from services.item_service import create_item
from services.log_service import (
    build_log_grid,
    get_logs_by_date,
    get_logs_by_date_range,
    take_all_fixed_dose,
    upsert_log_entry,
)


class FakeSupabaseClient:
    def __init__(self):
        self.logs = {}

    def upsert_log(self, *, timestamp, name, dose, unit, notes, category):
        self.logs[(timestamp, name)] = {
            "timestamp": timestamp,
            "name": name,
            "dose": dose,
            "unit": unit,
            "notes": notes,
            "category": category,
        }

    def list_logs(self, *, start_timestamp, end_timestamp):
        return [
            row
            for (timestamp, _), row in sorted(self.logs.items())
            if start_timestamp <= timestamp <= end_timestamp
        ]


def _create_item(name, default_dosage=None, dosage_unit="mg", sort_order=0):
    """Helper to create a test item and return its id."""
    return create_item(
        name=name,
        category="supplement",
        default_dosage=default_dosage,
        dosage_unit=dosage_unit,
        notes="",
    )


def test_upsert_log_entry_creates_new(test_db):
    """upsert_log_entry creates a new row when none exists."""
    item_id = _create_item("Vitamin C", default_dosage=500.0)
    upsert_log_entry("2025-01-15", item_id, 500.0)

    with db.get_connection() as conn:
        row = conn.execute(
            "SELECT dosage_taken FROM daily_logs WHERE log_date=? AND item_id=?",
            ("2025-01-15", item_id),
        ).fetchone()
        assert row is not None
        assert row["dosage_taken"] == 500.0


def test_upsert_log_entry_updates_existing(test_db):
    """upsert same (date, item_id) with new dosage updates in place."""
    item_id = _create_item("Vitamin C", default_dosage=500.0)
    upsert_log_entry("2025-01-15", item_id, 500.0)
    upsert_log_entry("2025-01-15", item_id, 750.0)

    with db.get_connection() as conn:
        rows = conn.execute(
            "SELECT dosage_taken FROM daily_logs WHERE log_date=? AND item_id=?",
            ("2025-01-15", item_id),
        ).fetchall()
        assert len(rows) == 1
        assert rows[0]["dosage_taken"] == 750.0


def test_upsert_default_dosage(test_db):
    """LOG-02: upsert writes default dosage for a fixed-dose item."""
    item_id = _create_item("Vitamin D", default_dosage=1000.0)
    upsert_log_entry("2025-01-15", item_id, 1000.0)

    with db.get_connection() as conn:
        row = conn.execute(
            "SELECT dosage_taken FROM daily_logs WHERE log_date=? AND item_id=?",
            ("2025-01-15", item_id),
        ).fetchone()
        assert row["dosage_taken"] == 1000.0


def test_upsert_custom_dosage(test_db):
    """LOG-03: upsert writes custom dosage overriding default."""
    item_id = _create_item("Vitamin D", default_dosage=1000.0)
    upsert_log_entry("2025-01-15", item_id, 500.0)

    with db.get_connection() as conn:
        row = conn.execute(
            "SELECT dosage_taken FROM daily_logs WHERE log_date=? AND item_id=?",
            ("2025-01-15", item_id),
        ).fetchone()
        assert row["dosage_taken"] == 500.0


def test_take_all_fixed_dose(test_db):
    """LOG-04: take-all inserts defaults only for unfilled active items."""
    id_a = _create_item("Item A", default_dosage=100.0)
    id_b = _create_item("Item B", default_dosage=200.0)
    id_c = _create_item("Item C")  # no default_dosage

    # Pre-log Item A
    upsert_log_entry("2025-01-15", id_a, 100.0)

    count = take_all_fixed_dose("2025-01-15")

    # Only Item B should get a new entry (Item A already logged, Item C has no default)
    assert count == 1

    with db.get_connection() as conn:
        row_a = conn.execute(
            "SELECT dosage_taken FROM daily_logs WHERE log_date=? AND item_id=?",
            ("2025-01-15", id_a),
        ).fetchone()
        assert row_a["dosage_taken"] == 100.0  # unchanged

        row_b = conn.execute(
            "SELECT dosage_taken FROM daily_logs WHERE log_date=? AND item_id=?",
            ("2025-01-15", id_b),
        ).fetchone()
        assert row_b["dosage_taken"] == 200.0  # default inserted

        row_c = conn.execute(
            "SELECT * FROM daily_logs WHERE log_date=? AND item_id=?",
            ("2025-01-15", id_c),
        ).fetchone()
        assert row_c is None  # no entry for no-default item


def test_log_entry_notes(test_db):
    """LOG-05: log entry can store an optional note."""
    item_id = _create_item("Vitamin C", default_dosage=500.0)
    upsert_log_entry("2025-01-15", item_id, 500.0, notes="with food")

    with db.get_connection() as conn:
        row = conn.execute(
            "SELECT notes FROM daily_logs WHERE log_date=? AND item_id=?",
            ("2025-01-15", item_id),
        ).fetchone()
        assert row["notes"] == "with food"


def test_get_logs_by_date(test_db):
    """LOG-06: get_logs_by_date returns only entries for the specified date."""
    id_a = _create_item("Item A", default_dosage=100.0)
    id_b = _create_item("Item B", default_dosage=200.0)

    upsert_log_entry("2025-01-15", id_a, 100.0)
    upsert_log_entry("2025-01-15", id_b, 200.0)
    upsert_log_entry("2025-01-16", id_a, 150.0)
    upsert_log_entry("2025-01-17", id_b, 250.0)

    logs = get_logs_by_date("2025-01-15")
    assert len(logs) == 2
    assert all(log["item_id"] in (id_a, id_b) for log in logs)


def test_build_log_grid(test_db):
    """LOG-01: build_log_grid returns a DataFrame with item names as columns."""
    id_a = _create_item("Item A", default_dosage=100.0)
    id_b = _create_item("Item B", default_dosage=200.0)

    upsert_log_entry("2025-01-15", id_a, 100.0)
    upsert_log_entry("2025-01-15", id_b, 200.0)

    df = build_log_grid("2025-01-15")
    assert len(df) == 1
    assert df.index[0] == "2025-01-15"
    assert "Item A" in df.columns
    assert "Item B" in df.columns
    assert df.loc["2025-01-15", "Item A"] == 100.0
    assert df.loc["2025-01-15", "Item B"] == 200.0


def test_build_log_grid_empty_date(test_db):
    """Grid for a date with no logs has 1 row with all NaN values."""
    _create_item("Item A", default_dosage=100.0)
    _create_item("Item B", default_dosage=200.0)

    df = build_log_grid("2025-01-15")
    assert len(df) == 1
    assert df.index[0] == "2025-01-15"
    assert df.isna().all().all()


def test_build_log_grid_sort_order(test_db):
    """CAT-10: grid columns ordered by sort_order, then name."""
    from services.item_service import update_item

    id_z = _create_item("Zebra Item", default_dosage=100.0)
    id_a = _create_item("Alpha Item", default_dosage=200.0)

    # Set sort_order: Alpha=2, Zebra=1 -> Zebra should come first
    update_item(id_z, sort_order=1)
    update_item(id_a, sort_order=2)

    upsert_log_entry("2025-01-15", id_z, 100.0)
    upsert_log_entry("2025-01-15", id_a, 200.0)

    df = build_log_grid("2025-01-15")
    columns = list(df.columns)
    assert columns[0] == "Zebra Item"
    assert columns[1] == "Alpha Item"


def test_get_logs_by_date_range(test_db):
    """DATA-02: get_logs_by_date_range returns multi-row DataFrame."""
    id_a = _create_item("Item A", default_dosage=100.0)
    id_b = _create_item("Item B", default_dosage=200.0)

    upsert_log_entry("2025-01-15", id_a, 100.0)
    upsert_log_entry("2025-01-15", id_b, 200.0)
    upsert_log_entry("2025-01-16", id_a, 150.0)
    upsert_log_entry("2025-01-17", id_b, 250.0)

    df = get_logs_by_date_range("2025-01-15", "2025-01-16")
    assert df.shape == (2, 2)  # 2 dates, 2 items
    assert df.loc["2025-01-15", "Item A"] == 100.0
    assert df.loc["2025-01-15", "Item B"] == 200.0
    assert df.loc["2025-01-16", "Item A"] == 150.0
    assert pd.isna(df.loc["2025-01-16", "Item B"])


def test_get_logs_by_date_range_empty(test_db):
    """get_logs_by_date_range with no logs returns empty DataFrame."""
    _create_item("Item A", default_dosage=100.0)
    df = get_logs_by_date_range("2025-06-01", "2025-06-03")
    assert df.empty


def test_upsert_log_entry_writes_to_supabase_when_enabled(test_db):
    """Supabase path denormalizes item metadata into medication_logs."""
    item_id = create_item("Aspirin", "medication", 81.0, "mg")
    client = FakeSupabaseClient()
    db.configure_supabase_client(client)
    db.configure_supabase_enabled(True)

    upsert_log_entry("2025-01-15", item_id, 81.0, notes="with food")

    assert client.logs == {
        ("2025-01-15T00:00:00Z", "Aspirin"): {
            "timestamp": "2025-01-15T00:00:00Z",
            "name": "Aspirin",
            "dose": 81.0,
            "unit": "mg",
            "notes": "with food",
            "category": "medication",
        }
    }


def test_supabase_reads_build_log_grid(test_db):
    """Grid reads use Supabase logs with the local catalog for ordering."""
    id_a = _create_item("Item A", default_dosage=100.0)
    id_b = _create_item("Item B", default_dosage=200.0)
    client = FakeSupabaseClient()
    db.configure_supabase_client(client)
    db.configure_supabase_enabled(True)

    upsert_log_entry("2025-01-15", id_b, 200.0)
    upsert_log_entry("2025-01-15", id_a, 100.0)

    df = build_log_grid("2025-01-15")

    assert list(df.columns) == ["Item A", "Item B"]
    assert df.loc["2025-01-15", "Item A"] == 100.0
    assert df.loc["2025-01-15", "Item B"] == 200.0


def test_supabase_get_logs_by_date_range_builds_export_dataframe(test_db):
    """Supabase range reads still return the CSV/export dataframe shape."""
    id_a = _create_item("Item A", default_dosage=100.0)
    id_b = _create_item("Item B", default_dosage=200.0)
    client = FakeSupabaseClient()
    db.configure_supabase_client(client)
    db.configure_supabase_enabled(True)

    upsert_log_entry("2025-01-15", id_a, 100.0)
    upsert_log_entry("2025-01-15", id_b, 200.0)
    upsert_log_entry("2025-01-16", id_a, 150.0)

    df = get_logs_by_date_range("2025-01-15", "2025-01-16")

    assert df.shape == (2, 2)
    assert df.loc["2025-01-15", "Item A"] == 100.0
    assert df.loc["2025-01-15", "Item B"] == 200.0
    assert df.loc["2025-01-16", "Item A"] == 150.0
    assert pd.isna(df.loc["2025-01-16", "Item B"])


def test_supabase_take_all_fixed_dose_skips_existing(test_db):
    """Take-all checks Supabase before writing default doses."""
    id_a = _create_item("Item A", default_dosage=100.0)
    _create_item("Item B", default_dosage=200.0)
    _create_item("Item C")
    client = FakeSupabaseClient()
    db.configure_supabase_client(client)
    db.configure_supabase_enabled(True)

    upsert_log_entry("2025-01-15", id_a, 100.0)
    count = take_all_fixed_dose("2025-01-15")

    assert count == 1
    rows_by_name = {row["name"]: row for row in client.logs.values()}
    assert set(rows_by_name) == {"Item A", "Item B"}
    assert rows_by_name["Item B"]["dose"] == 200.0

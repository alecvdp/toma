"""Tests for import validation and upsert functionality."""

import pandas as pd

import db
from services.import_service import import_logs, validate_import
from services.item_service import create_item


def _create_item(name, default_dosage=None, dosage_unit="mg"):
    """Helper to create a test item and return its id."""
    return create_item(
        name=name,
        category="supplement",
        default_dosage=default_dosage,
        dosage_unit=dosage_unit,
        notes="",
    )


def _get_active_items():
    """Helper to fetch active items."""
    from services.item_service import get_active_items

    return get_active_items()


def test_validate_import_valid(test_db):
    """DATA-04: valid DataFrame with date + matching item columns passes."""
    _create_item("Item A", default_dosage=100.0)
    _create_item("Item B", default_dosage=200.0)

    df = pd.DataFrame({"date": ["2025-01-15"], "Item A": [100.0], "Item B": [200.0]})
    is_valid, messages = validate_import(df, _get_active_items())
    assert is_valid is True
    assert messages == []


def test_validate_import_missing_date(test_db):
    """validate_import rejects DataFrame without 'date' column."""
    _create_item("Item A")

    df = pd.DataFrame({"Item A": [100.0]})
    is_valid, messages = validate_import(df, _get_active_items())
    assert is_valid is False
    assert any("date" in msg.lower() for msg in messages)


def test_validate_import_unrecognized_columns(test_db):
    """validate_import warns about unrecognized item columns."""
    _create_item("Item A")

    df = pd.DataFrame(
        {"date": ["2025-01-15"], "Item A": [100.0], "Unknown Item": [50.0]}
    )
    is_valid, messages = validate_import(df, _get_active_items())
    assert is_valid is True
    assert any("Unknown Item" in msg for msg in messages)


def test_validate_import_no_matches(test_db):
    """validate_import rejects DataFrame with NO matching item columns."""
    _create_item("Item A")

    df = pd.DataFrame({"date": ["2025-01-15"], "Bogus": [100.0]})
    is_valid, messages = validate_import(df, _get_active_items())
    assert is_valid is False


def test_import_logs(test_db):
    """DATA-04: import_logs upserts entries for matched items."""
    id_a = _create_item("Item A", default_dosage=100.0)
    id_b = _create_item("Item B", default_dosage=200.0)

    df = pd.DataFrame(
        {
            "date": ["2025-01-15", "2025-01-16"],
            "Item A": [100.0, 150.0],
            "Item B": [200.0, 250.0],
        }
    )
    count = import_logs(df, _get_active_items())
    assert count == 4  # 2 dates * 2 items

    with db.get_connection() as conn:
        row = conn.execute(
            "SELECT dosage_taken FROM daily_logs WHERE log_date=? AND item_id=?",
            ("2025-01-15", id_a),
        ).fetchone()
        assert row["dosage_taken"] == 100.0

        row = conn.execute(
            "SELECT dosage_taken FROM daily_logs WHERE log_date=? AND item_id=?",
            ("2025-01-16", id_b),
        ).fetchone()
        assert row["dosage_taken"] == 250.0


def test_import_logs_skips_unknown(test_db):
    """import_logs skips unrecognized item columns without error."""
    id_a = _create_item("Item A", default_dosage=100.0)

    df = pd.DataFrame(
        {"date": ["2025-01-15"], "Item A": [100.0], "Unknown Item": [50.0]}
    )
    count = import_logs(df, _get_active_items())
    assert count == 1  # Only Item A imported

    with db.get_connection() as conn:
        row = conn.execute(
            "SELECT dosage_taken FROM daily_logs WHERE log_date=? AND item_id=?",
            ("2025-01-15", id_a),
        ).fetchone()
        assert row["dosage_taken"] == 100.0

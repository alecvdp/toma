"""Tests for database schema and persistence."""

import sqlite3

import pytest

import db


def test_init_db_creates_items_table(test_db):
    """After init_db(), the items table exists."""
    with db.get_connection() as conn:
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='items'"
        )
        assert cursor.fetchone() is not None


def test_persistence(test_db):
    """Data persists across connections."""
    with db.get_connection() as conn:
        conn.execute(
            "INSERT INTO items (name) VALUES (?)",
            ("Vitamin C",),
        )

    # New connection should see the data
    with db.get_connection() as conn:
        row = conn.execute("SELECT name FROM items WHERE name='Vitamin C'").fetchone()
        assert row is not None
        assert row["name"] == "Vitamin C"


def test_init_db_creates_daily_logs_table(test_db):
    """After init_db(), the daily_logs table exists."""
    with db.get_connection() as conn:
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='daily_logs'"
        )
        assert cursor.fetchone() is not None


def test_daily_logs_unique_constraint(test_db):
    """UNIQUE(log_date, item_id) prevents duplicate entries."""
    with db.get_connection() as conn:
        conn.execute("INSERT INTO items (name) VALUES ('Vitamin D')")
        item_id = conn.execute("SELECT id FROM items WHERE name='Vitamin D'").fetchone()["id"]
        conn.execute(
            "INSERT INTO daily_logs (log_date, item_id, dosage_taken) VALUES (?, ?, ?)",
            ("2025-01-15", item_id, 500.0),
        )

    with pytest.raises(sqlite3.IntegrityError):
        with db.get_connection() as conn:
            conn.execute(
                "INSERT INTO daily_logs (log_date, item_id, dosage_taken) VALUES (?, ?, ?)",
                ("2025-01-15", item_id, 1000.0),
            )


def test_daily_logs_foreign_key(test_db):
    """Foreign key constraint prevents inserting with non-existent item_id."""
    with pytest.raises(sqlite3.IntegrityError):
        with db.get_connection() as conn:
            conn.execute(
                "INSERT INTO daily_logs (log_date, item_id, dosage_taken) VALUES (?, ?, ?)",
                ("2025-01-15", 9999, 500.0),
            )

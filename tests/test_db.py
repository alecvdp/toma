"""Tests for database schema and persistence."""

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

"""Test fixtures for Toma."""

import pytest

import db


@pytest.fixture
def test_db(tmp_path):
    """Provide an isolated SQLite database for each test."""
    test_db_path = tmp_path / "test_toma.db"
    original_path = db.DB_PATH
    db.DB_PATH = test_db_path
    db.configure_supabase_enabled(False)
    db.configure_supabase_client(None)
    db.init_db()
    yield test_db_path
    db.DB_PATH = original_path
    db.configure_supabase_enabled(None)
    db.configure_supabase_client(None)

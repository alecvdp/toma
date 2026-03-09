"""Tests for item_service CRUD operations."""

import sqlite3

import pytest

from services.item_service import (
    create_item,
    deactivate_item,
    get_active_items,
    get_categories,
    get_item,
    search_items,
    update_item,
)


def test_create_item(test_db):
    """create_item returns an integer id > 0."""
    item_id = create_item("Vitamin D", "supplement", 5000.0, "IU", "Daily")
    assert isinstance(item_id, int)
    assert item_id > 0


def test_create_item_duplicate_name(test_db):
    """Creating an item with the same name twice raises IntegrityError."""
    create_item("Vitamin D", "supplement", 5000.0, "IU")
    with pytest.raises(sqlite3.IntegrityError):
        create_item("Vitamin D", "supplement", 5000.0, "IU")


def test_get_item(test_db):
    """get_item returns a dict with all fields."""
    item_id = create_item("Vitamin D", "supplement", 5000.0, "IU", "Daily")
    item = get_item(item_id)
    assert item is not None
    assert item["name"] == "Vitamin D"
    assert item["category"] == "supplement"
    assert item["default_dosage"] == 5000.0
    assert item["dosage_unit"] == "IU"
    assert item["notes"] == "Daily"
    assert item["is_active"] == 1


def test_get_active_items(test_db):
    """Returns only active items, ordered by name."""
    create_item("Zinc", "supplement", 30.0, "mg")
    create_item("Aspirin", "medication", 81.0, "mg")
    id3 = create_item("Fish Oil", "supplement", 1000.0, "mg")
    deactivate_item(id3)

    items = get_active_items()
    names = [i["name"] for i in items]
    assert names == ["Aspirin", "Zinc"]


def test_update_item(test_db):
    """update_item changes specified fields and updates updated_at."""
    item_id = create_item("Vitamin D", "supplement", 5000.0, "IU")
    original = get_item(item_id)

    update_item(item_id, name="Vitamin D3")
    updated = get_item(item_id)

    assert updated["name"] == "Vitamin D3"
    assert updated["updated_at"] >= original["updated_at"]


def test_deactivate_item(test_db):
    """deactivate_item sets is_active=0."""
    item_id = create_item("Vitamin D", "supplement", 5000.0, "IU")
    deactivate_item(item_id)

    item = get_item(item_id)
    assert item["is_active"] == 0

    active = get_active_items()
    assert all(i["id"] != item_id for i in active)


def test_item_category(test_db):
    """Item stores category correctly and it can be updated."""
    item_id = create_item("Aspirin", "medication", 81.0, "mg")
    assert get_item(item_id)["category"] == "medication"

    update_item(item_id, category="supplement")
    assert get_item(item_id)["category"] == "supplement"


def test_default_dosage(test_db):
    """Item stores dosage and unit; both can be None/nullable."""
    item_id = create_item("Vitamin D", "supplement", 5000.0, "IU")
    item = get_item(item_id)
    assert item["default_dosage"] == 5000.0
    assert item["dosage_unit"] == "IU"

    # Dosage can be set to None
    id2 = create_item("Misc", "supplement", None, "mg")
    assert get_item(id2)["default_dosage"] is None


def test_item_notes(test_db):
    """Create with notes, update notes."""
    item_id = create_item("Vitamin D", "supplement", 5000.0, "IU", "Take with food")
    assert get_item(item_id)["notes"] == "Take with food"

    update_item(item_id, notes="Take in morning")
    assert get_item(item_id)["notes"] == "Take in morning"


def test_search_items_by_name(test_db):
    """search_items matches name substring."""
    create_item("Vitamin D", "supplement", 5000.0, "IU")
    create_item("Fish Oil", "supplement", 1000.0, "mg")

    results = search_items(query="vita")
    assert len(results) == 1
    assert results[0]["name"] == "Vitamin D"


def test_search_items_by_category(test_db):
    """search_items filters by category."""
    create_item("Vitamin D", "supplement", 5000.0, "IU")
    create_item("Aspirin", "prescription", 81.0, "mg")

    results = search_items(category="prescription")
    assert len(results) == 1
    assert results[0]["name"] == "Aspirin"


def test_search_items_combined(test_db):
    """search_items filters by both name and category."""
    create_item("Vitamin D", "supplement", 5000.0, "IU")
    create_item("Vitamin C", "prescription", 500.0, "mg")
    create_item("Fish Oil", "supplement", 1000.0, "mg")

    results = search_items(query="vita", category="supplement")
    assert len(results) == 1
    assert results[0]["name"] == "Vitamin D"


def test_get_categories(test_db):
    """Returns distinct categories from active items only."""
    create_item("Vitamin D", "supplement", 5000.0, "IU")
    id2 = create_item("Aspirin", "prescription", 81.0, "mg")
    create_item("Fish Oil", "supplement", 1000.0, "mg")

    cats = get_categories()
    assert set(cats) == {"supplement", "prescription"}

    # Deactivate the only prescription item
    deactivate_item(id2)
    cats = get_categories()
    assert set(cats) == {"supplement"}

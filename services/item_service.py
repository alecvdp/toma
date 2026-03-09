"""Catalog CRUD operations for items."""


def create_item(name, category, default_dosage, dosage_unit, notes=""):
    """Create a new item and return its id."""
    raise NotImplementedError("TODO")


def get_item(item_id):
    """Get an item by id, return dict or None."""
    raise NotImplementedError("TODO")


def get_active_items():
    """Get all active items ordered by name."""
    raise NotImplementedError("TODO")


def update_item(item_id, **kwargs):
    """Update specified fields on an item."""
    raise NotImplementedError("TODO")


def deactivate_item(item_id):
    """Soft-delete an item by setting is_active=0."""
    raise NotImplementedError("TODO")


def search_items(query="", category=""):
    """Search items by name substring and/or category."""
    raise NotImplementedError("TODO")


def get_categories():
    """Get distinct categories from active items."""
    raise NotImplementedError("TODO")

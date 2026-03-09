"""Catalog CRUD operations for items."""

from db import get_connection


def create_item(name, category, default_dosage, dosage_unit, notes=""):
    """Create a new item and return its id."""
    with get_connection() as conn:
        cursor = conn.execute(
            """INSERT INTO items (name, category, default_dosage, dosage_unit, notes)
               VALUES (?, ?, ?, ?, ?)""",
            (name, category, default_dosage, dosage_unit, notes),
        )
        return cursor.lastrowid


def get_item(item_id):
    """Get an item by id, return dict or None."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM items WHERE id = ?", (item_id,)
        ).fetchone()
        return dict(row) if row else None


def get_active_items():
    """Get all active items ordered by name."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM items WHERE is_active = 1 ORDER BY name"
        ).fetchall()
        return [dict(r) for r in rows]


def update_item(item_id, **kwargs):
    """Update specified fields on an item."""
    if not kwargs:
        return
    set_clauses = ", ".join(f"{key} = ?" for key in kwargs)
    values = list(kwargs.values())
    values.append(item_id)
    with get_connection() as conn:
        conn.execute(
            f"UPDATE items SET {set_clauses}, updated_at = datetime('now') WHERE id = ?",
            values,
        )


def deactivate_item(item_id):
    """Soft-delete an item by setting is_active=0."""
    with get_connection() as conn:
        conn.execute(
            "UPDATE items SET is_active = 0, updated_at = datetime('now') WHERE id = ?",
            (item_id,),
        )


def search_items(query="", category=""):
    """Search items by name substring and/or category."""
    conditions = ["is_active = 1"]
    params = []
    if query:
        conditions.append("name LIKE ?")
        params.append(f"%{query}%")
    if category:
        conditions.append("category = ?")
        params.append(category)
    where = " AND ".join(conditions)
    with get_connection() as conn:
        rows = conn.execute(
            f"SELECT * FROM items WHERE {where} ORDER BY name", params
        ).fetchall()
        return [dict(r) for r in rows]


def get_categories():
    """Get distinct categories from active items."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT DISTINCT category FROM items WHERE is_active = 1 ORDER BY category"
        ).fetchall()
        return [r["category"] for r in rows]

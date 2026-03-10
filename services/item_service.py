"""Catalog CRUD operations for items."""

import json
import urllib.parse
import urllib.request

from db import get_connection


def fetch_wikipedia_description(search_term: str) -> str | None:
    """Fetch a 1-3 sentence description from Wikipedia.

    Uses a two-step approach: opensearch to resolve the correct title,
    then the REST summary API to get the extract text.

    Returns the extract text (max 3 sentences) or None on any error.
    """
    try:
        headers = {"User-Agent": "Toma/1.0 (personal medication tracker)"}

        # Step 1: Search for the correct title via opensearch
        encoded = urllib.parse.quote(search_term)
        search_url = (
            f"https://en.wikipedia.org/w/api.php"
            f"?action=opensearch&search={encoded}&limit=1&format=json"
        )
        req = urllib.request.Request(search_url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())

        if not data[1]:  # no search results
            return None

        # Step 2: Fetch summary using the resolved title
        title = data[1][0].replace(" ", "_")
        summary_url = (
            f"https://en.wikipedia.org/api/rest_v1/page/summary/"
            f"{urllib.parse.quote(title)}"
        )
        req = urllib.request.Request(summary_url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as resp:
            summary = json.loads(resp.read())

        extract = summary.get("extract", "")
        if not extract:
            return None

        # Truncate to 3 sentences
        sentences = extract.split(". ")
        if len(sentences) <= 3:
            return extract
        return ". ".join(sentences[:3]) + "."

    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError, OSError):
        return None


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

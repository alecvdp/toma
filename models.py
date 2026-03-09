"""Data models for Toma."""

import sqlite3
from dataclasses import dataclass


@dataclass
class Item:
    """Represents a medication or supplement catalog item."""

    id: int | None
    name: str
    category: str
    default_dosage: float | None
    dosage_unit: str
    description: str
    notes: str
    sort_order: int
    is_active: bool
    created_at: str | None
    updated_at: str | None

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Item":
        """Create an Item from a sqlite3.Row."""
        return cls(
            id=row["id"],
            name=row["name"],
            category=row["category"],
            default_dosage=row["default_dosage"],
            dosage_unit=row["dosage_unit"],
            description=row["description"],
            notes=row["notes"],
            sort_order=row["sort_order"],
            is_active=bool(row["is_active"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

"""Tests for CSV export functionality."""

import pandas as pd

from services.log_service import export_logs_csv


def test_export_logs_csv():
    """DATA-03: export_logs_csv produces valid CSV bytes with correct headers."""
    df = pd.DataFrame(
        {"Item A": [100.0, 150.0], "Item B": [200.0, None]},
        index=["2025-01-15", "2025-01-16"],
    )
    df.index.name = "date"

    result = export_logs_csv(df)
    assert isinstance(result, bytes)

    text = result.decode("utf-8")
    lines = text.strip().split("\n")
    assert lines[0] == "date,Item A,Item B"
    assert "2025-01-15" in lines[1]
    assert "100.0" in lines[1]

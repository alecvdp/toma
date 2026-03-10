"""Import / Export page - upload CSV/Excel data and download logs."""

from datetime import date, timedelta

import pandas as pd
import streamlit as st

from services.import_service import import_logs, validate_import
from services.item_service import get_active_items
from services.log_service import export_logs_csv, get_logs_by_date_range

st.title("Import / Export")

# --- Export Section (DATA-03) ---
st.subheader("Export")

export_range = st.date_input(
    "Export date range",
    value=(date.today() - timedelta(days=30), date.today()),
    max_value=date.today(),
    key="export_range",
)

if len(export_range) == 2:
    export_start, export_end = export_range
    export_df = get_logs_by_date_range(
        export_start.strftime("%Y-%m-%d"), export_end.strftime("%Y-%m-%d")
    )
    if not export_df.empty:
        st.dataframe(export_df, use_container_width=True)
        st.download_button(
            "Download CSV",
            data=export_logs_csv(export_df),
            file_name=f"toma_export_{export_start}_{export_end}.csv",
            mime="text/csv",
        )
    else:
        st.info("No log entries in this date range.")

# --- Import Section (DATA-04) ---
st.divider()
st.subheader("Import")

uploaded_file = st.file_uploader(
    "Upload CSV or Excel file", type=["csv", "xlsx"], key="import_file"
)

if uploaded_file is not None:
    # Read the file based on extension
    if uploaded_file.name.endswith(".xlsx"):
        import_df = pd.read_excel(uploaded_file, engine="openpyxl")
    else:
        import_df = pd.read_csv(uploaded_file)

    # Validate against active catalog
    active_items = get_active_items()
    is_valid, messages = validate_import(import_df, active_items)

    if not is_valid:
        for msg in messages:
            st.error(msg)
    else:
        if messages:
            for msg in messages:
                st.warning(msg)

        # Preview
        st.write("**Preview** (first 10 rows):")
        st.dataframe(import_df.head(10), use_container_width=True)

        # Summary
        item_columns = [
            c
            for c in import_df.columns
            if c != "date" and c in {item["name"] for item in active_items}
        ]
        non_null_count = import_df[item_columns].notna().sum().sum()
        st.write(
            f"Will import up to **{int(non_null_count)} entries** "
            f"for **{len(item_columns)} items** "
            f"across **{len(import_df)} dates**."
        )

        # Confirm button
        if st.button("Confirm Import"):
            count = import_logs(import_df, active_items)
            st.success(f"Imported {count} entries.")

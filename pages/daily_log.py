"""Daily log page - editable grid, Take All, date navigation, and notes."""

from datetime import date

import streamlit as st

from services.item_service import get_active_items
from services.log_service import (
    build_log_grid,
    get_logs_by_date,
    take_all_fixed_dose,
    upsert_log_entry,
)

st.title("Daily Log")

# --- Date Navigation (LOG-06) ---
selected_date = st.date_input("Date", value=date.today())
log_date_str = selected_date.strftime("%Y-%m-%d")

# --- Build item lookup: name -> item dict ---
active_items = get_active_items()
# Sort by sort_order then name for consistent column ordering
active_items_sorted = sorted(active_items, key=lambda x: (x.get("sort_order") or 0, x["name"]))
item_lookup = {item["name"]: item for item in active_items_sorted}

# --- Take All Button (LOG-04) ---
if st.button("Take All Defaults"):
    count = take_all_fixed_dose(log_date_str)
    if count > 0:
        st.toast(f"Filled {count} item(s) with default dosages.")
    else:
        st.toast("All items already logged for this date.")
    st.rerun()

# --- Grid (LOG-01, LOG-02, LOG-03, CAT-10) ---
if not active_items:
    st.info("No items in catalog. Add items in the Catalog page first.")
else:
    grid_df = build_log_grid(log_date_str)

    # Build column config with NumberColumn for each item
    col_config = {}
    for item_name, item in item_lookup.items():
        help_text = None
        if item.get("default_dosage"):
            help_text = f"Default: {item['default_dosage']} {item.get('dosage_unit', '')}"
        col_config[item_name] = st.column_config.NumberColumn(
            item_name,
            help=help_text,
            min_value=0.0,
            format="%.1f",
        )

    # Column order follows sort_order (grid_df columns already ordered by build_log_grid)
    column_order = list(grid_df.columns)

    edited_df = st.data_editor(
        grid_df,
        key="log_grid",
        column_config=col_config,
        column_order=column_order,
        hide_index=False,
        num_rows="fixed",
        use_container_width=True,
    )

    # --- Handle edits via comparing DataFrames ---
    # st.data_editor returns the edited DataFrame; compare with original to find changes
    if st.session_state.get("log_grid") and st.session_state["log_grid"].get("edited_rows"):
        for row_idx_str, changes in st.session_state["log_grid"]["edited_rows"].items():
            for item_name, new_value in changes.items():
                if item_name in item_lookup:
                    item = item_lookup[item_name]
                    upsert_log_entry(log_date_str, item["id"], new_value)

# --- Notes Section (LOG-05) ---
st.subheader("Entry Notes")

log_entries = get_logs_by_date(log_date_str)
logged_entries = [e for e in log_entries if e["dosage_taken"] is not None]

if not logged_entries:
    st.caption("No logged entries for this date yet. Use the grid above to log dosages.")
else:
    for entry in logged_entries:
        new_note = st.text_input(
            f"{entry['item_name']}",
            value=entry.get("notes") or "",
            key=f"note_{entry['item_id']}",
        )
        # Persist note changes
        current_note = entry.get("notes") or ""
        if new_note != current_note:
            upsert_log_entry(
                log_date_str,
                entry["item_id"],
                entry["dosage_taken"],
                notes=new_note,
            )

# --- Legend ---
st.caption("Empty = not yet logged. 0 = skipped. Any number = dosage taken.")

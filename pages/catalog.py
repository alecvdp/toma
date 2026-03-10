"""Catalog management page - add, edit, delete, search, and filter items."""

import streamlit as st

from services.item_service import (
    create_item,
    deactivate_item,
    fetch_wikipedia_description,
    get_categories,
    get_item,
    search_items,
    update_item,
)

st.title("Catalog")

# --- Constants ---
CATEGORIES = ["supplement", "prescription", "vitamin", "other"]
DOSAGE_UNITS = ["mg", "mcg", "IU", "mL", "capsule", "tablet"]

# --- Initialize session state ---
if "editing_item" not in st.session_state:
    st.session_state.editing_item = None
if "deleting_item" not in st.session_state:
    st.session_state.deleting_item = None
if "fetched_description" not in st.session_state:
    st.session_state.fetched_description = ""
if "edit_fetched_description" not in st.session_state:
    st.session_state.edit_fetched_description = None

# --- Search and Filter Bar ---
col_search, col_filter = st.columns([3, 1])
with col_search:
    search_query = st.text_input("Search by name", key="search_query")
with col_filter:
    existing_categories = get_categories()
    category_options = ["All"] + existing_categories
    selected_category = st.selectbox("Filter by category", options=category_options, key="category_filter")

filter_category = "" if selected_category == "All" else selected_category
items = search_items(query=search_query, category=filter_category)

# --- Add Item Form ---
with st.expander("Add New Item"):
    # Fetch Description button (outside form for dynamic interaction)
    fetch_col1, fetch_col2 = st.columns([3, 1])
    with fetch_col1:
        fetch_name = st.text_input("Item name to look up", key="fetch_name_input")
    with fetch_col2:
        st.write("")  # spacing
        if st.button("Fetch Description", key="fetch_add_desc"):
            if fetch_name.strip():
                with st.spinner("Fetching from Wikipedia..."):
                    desc = fetch_wikipedia_description(fetch_name.strip())
                if desc:
                    st.session_state.fetched_description = desc
                    st.success("Description fetched from Wikipedia.")
                else:
                    st.warning("No Wikipedia description found. You can enter one manually.")
            else:
                st.warning("Enter an item name first.")

    with st.form("add_item_form", clear_on_submit=True):
        add_name = st.text_input("Name")
        add_category = st.selectbox("Category", options=CATEGORIES, key="add_category")
        add_dosage = st.number_input("Default Dosage", min_value=0.0, step=0.1, key="add_dosage")
        add_unit = st.selectbox("Dosage Unit", options=DOSAGE_UNITS, key="add_unit")
        add_description = st.text_area(
            "Description",
            value=st.session_state.fetched_description,
            key="add_description",
            help="Auto-fetch from Wikipedia or type your own description.",
        )
        add_notes = st.text_area("Notes", key="add_notes")
        submitted = st.form_submit_button("Add Item")
        if submitted:
            if not add_name.strip():
                st.error("Name is required.")
            else:
                dosage_value = add_dosage if add_dosage > 0 else None
                item_id = create_item(
                    name=add_name.strip(),
                    category=add_category,
                    default_dosage=dosage_value,
                    dosage_unit=add_unit,
                    notes=add_notes,
                )
                if add_description.strip():
                    update_item(item_id, description=add_description.strip())
                st.session_state.fetched_description = ""
                st.success(f"Added '{add_name.strip()}' to catalog.")
                st.rerun()

# --- Edit Item Form ---
if st.session_state.editing_item is not None:
    item = get_item(st.session_state.editing_item)
    if item:
        st.subheader(f"Edit: {item['name']}")

        # Fetch Description button for edit (outside form)
        edit_fetch_col1, edit_fetch_col2 = st.columns([3, 1])
        with edit_fetch_col2:
            st.write("")  # spacing
            if st.button("Fetch Description", key="fetch_edit_desc"):
                with st.spinner("Fetching from Wikipedia..."):
                    desc = fetch_wikipedia_description(item["name"])
                if desc:
                    st.session_state.edit_fetched_description = desc
                    st.success("Description fetched from Wikipedia.")
                else:
                    st.warning("No Wikipedia description found.")

        # Determine description default: use fetched if available, else existing
        edit_desc_value = (
            st.session_state.edit_fetched_description
            if st.session_state.edit_fetched_description is not None
            else (item["description"] or "")
        )

        with st.form("edit_item_form"):
            edit_name = st.text_input("Name", value=item["name"])
            edit_category = st.selectbox(
                "Category",
                options=CATEGORIES,
                index=CATEGORIES.index(item["category"]) if item["category"] in CATEGORIES else 0,
                key="edit_category",
            )
            edit_dosage = st.number_input(
                "Default Dosage",
                min_value=0.0,
                step=0.1,
                value=float(item["default_dosage"]) if item["default_dosage"] else 0.0,
                key="edit_dosage",
            )
            edit_unit = st.selectbox(
                "Dosage Unit",
                options=DOSAGE_UNITS,
                index=DOSAGE_UNITS.index(item["dosage_unit"]) if item["dosage_unit"] in DOSAGE_UNITS else 0,
                key="edit_unit",
            )
            edit_description = st.text_area(
                "Description",
                value=edit_desc_value,
                key="edit_description",
                help="Auto-fetch from Wikipedia or edit manually.",
            )
            edit_notes = st.text_area("Notes", value=item["notes"] or "", key="edit_notes")

            col_save, col_cancel = st.columns(2)
            with col_save:
                save_clicked = st.form_submit_button("Save")
            with col_cancel:
                cancel_clicked = st.form_submit_button("Cancel")

            if save_clicked:
                if not edit_name.strip():
                    st.error("Name is required.")
                else:
                    dosage_value = edit_dosage if edit_dosage > 0 else None
                    update_item(
                        st.session_state.editing_item,
                        name=edit_name.strip(),
                        category=edit_category,
                        default_dosage=dosage_value,
                        dosage_unit=edit_unit,
                        description=edit_description,
                        notes=edit_notes,
                    )
                    st.session_state.editing_item = None
                    st.session_state.edit_fetched_description = None
                    st.rerun()
            if cancel_clicked:
                st.session_state.editing_item = None
                st.session_state.edit_fetched_description = None
                st.rerun()
    else:
        st.session_state.editing_item = None
        st.rerun()

# --- Delete Confirmation ---
if st.session_state.deleting_item is not None:
    item = get_item(st.session_state.deleting_item)
    if item:
        st.warning(f"Delete '{item['name']}'? This will remove it from the active catalog.")
        col_confirm, col_cancel_del = st.columns(2)
        with col_confirm:
            if st.button("Confirm Delete", type="primary"):
                deactivate_item(st.session_state.deleting_item)
                st.session_state.deleting_item = None
                st.rerun()
        with col_cancel_del:
            if st.button("Cancel"):
                st.session_state.deleting_item = None
                st.rerun()
    else:
        st.session_state.deleting_item = None
        st.rerun()

# --- Card View ---
if not items:
    st.info("No items found. Add one above to get started!")
else:
    for item in items:
        with st.container(border=True):
            col_info, col_dosage, col_actions = st.columns([3, 1, 1])
            with col_info:
                st.subheader(item["name"])
                if item.get("description"):
                    st.caption(item["description"])
                if item.get("notes"):
                    st.text(item["notes"])
            with col_dosage:
                if item.get("default_dosage"):
                    st.metric("Dosage", f"{item['default_dosage']} {item['dosage_unit']}")
                st.badge(item["category"])
            with col_actions:
                if st.button("Edit", key=f"edit_{item['id']}"):
                    st.session_state.editing_item = item["id"]
                    st.rerun()
                if st.button("Delete", key=f"delete_{item['id']}"):
                    st.session_state.deleting_item = item["id"]
                    st.rerun()

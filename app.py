"""Toma - Medication and Supplement Tracker."""

import streamlit as st

from db import init_db

init_db()

daily_log_page = st.Page("pages/daily_log.py", title="Daily Log", icon=":material/edit_note:", default=True)
catalog_page = st.Page("pages/catalog.py", title="Catalog", icon=":material/medication:")
pg = st.navigation([daily_log_page, catalog_page])
pg.run()

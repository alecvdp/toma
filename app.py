"""Toma - Medication and Supplement Tracker."""

import streamlit as st

from db import init_db

init_db()

catalog_page = st.Page("pages/catalog.py", title="Catalog", icon=":material/medication:")
pg = st.navigation([catalog_page])
pg.run()

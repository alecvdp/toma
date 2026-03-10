# Deferred Items - Phase 03

## Pre-existing Issues

1. **test_log_service.py imports `export_logs_csv` which does not exist yet** - This function is part of DATA-03 (03-02-PLAN). The import causes a collection error when running `pytest tests/ -x`. Tests pass when excluding this file. Will be resolved when 03-02 plan implements the export feature.

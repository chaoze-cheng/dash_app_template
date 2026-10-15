# UI-002 — AG Grid Server-Side Pagination

- **Status:** experimental
- **Purpose:** Illustrate Callback → Service → DB layering with paginated AG Grid.
- **Dependencies:** Dash, dash-ag-grid, pandas.
- **Run:** `python app.py` from this directory; example uses in-memory demo data instead of PostgreSQL.
- **Interfaces:** `get_page(start_row, end_row, sort_model)` returns `(rows, total_count)`; `fetch_rows(...)` is a DB-layer demonstration adapter.
- **Integration:** Replace the demo `db.py` adapter with ConnectorX/SQLAlchemy queries in target `src/db/`; move service and callbacks to matching project directories; enforce visibility in SQL.
- **Limitations:** Demonstrates AG Grid infinite row model (not enterprise-only server-side row model); does not implement filterModel, authorization or real database pagination. API compatibility must be checked with installed dash-ag-grid version.
- **Source/License:** Original scaffold; no third-party project code included.
- **Verification:** Not tested against deployed Dash/AG Grid versions.

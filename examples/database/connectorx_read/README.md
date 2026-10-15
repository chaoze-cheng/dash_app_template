# DB-001 — ConnectorX Read

- **Status:** experimental
- **Purpose:** Encapsulate ConnectorX read-only queries in a DB-layer module.
- **Dependencies:** `connectorx`, `pandas`, PostgreSQL connection URI.
- **Run:** Requires a configured development database; no live DB test is included.
- **Interface:** `read_public_items(uri, limit=100)` returns pandas DataFrame.
- **Security:** Demonstrates an allowlisted, bounded integer limit. Never interpolate user text into SQL; for general user-controlled filters use SQLAlchemy parameter binding instead.
- **Integration:** Move `queries.py` to `src/db/queries/`; Services call this function, never Dash Callback directly.
- **Limitations:** Requires example `items` table with `visibility` column; adjust table/columns to the target schema; connection handling and permissions must be reviewed.
- **Source/License:** Original scaffold; no third-party project code included.
- **Verification:** Not tested against a real database.

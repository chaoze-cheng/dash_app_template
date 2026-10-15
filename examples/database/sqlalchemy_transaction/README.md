# DB-002 — SQLAlchemy Transaction

- **Status:** experimental
- **Purpose:** Demonstrate a SQLAlchemy 2.x session factory and atomic write transaction.
- **Dependencies:** `sqlalchemy>=2,<3` and a database driver.
- **Run:** `python example.py` uses in-memory SQLite for demonstration only; target production backend remains PostgreSQL.
- **Interface:** `create_engine_and_session(url)`, `create_item(session_factory, name)`.
- **Integration:** Move model, session, query and service functions to the target project's `src/db/` and `src/services/` respectively; manage migrations with Alembic.
- **Limitations:** Not a production schema, no RBAC, no real PostgreSQL validation.
- **Source/License:** Original scaffold; no third-party project code included.
- **Verification:** Not tested against a production database.

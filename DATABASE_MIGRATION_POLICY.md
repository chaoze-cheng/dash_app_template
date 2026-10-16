# Database Migration Safety & Multi-Agent Policy

> Status: Proposed / documentation only (2026-10-16). This document specifies desired safeguards; **it does not mean any safeguard is already implemented**.
>
> Stack: PostgreSQL 16, SQLAlchemy 2.0, Alembic, Python 3.12, Dash/Flask, Docker. Normative terms: **MUST**, **SHOULD**, **MAY**.

## 1. Fundamental policy

1. **MUST** treat Alembic as the single source of truth for database schema changes. Initialization of a fresh managed database uses `alembic upgrade head`, not ORM `create_all()`.
2. **MUST NOT** call `Base.metadata.create_all()`, `drop_all()`, `DROP SCHEMA`, `DROP DATABASE`, `TRUNCATE`, `dropdb`, database-volume deletion, or database recreation from application startup, callback, CLI auto-repair, tests connected to shared databases, or normal deployment scripts. These operations require a dedicated, manually authorized maintenance workflow (and some should remain entirely forbidden for persistent environments).
3. **MUST** be *forward-only* in normal development and deployment: upgrades use approved new revisions; `downgrade` is not an automated recovery procedure. Existing deployed revisions remain immutable. `alembic stamp` is forbidden as an automatic reconciliation mechanism.
4. **MUST NOT** create, generate, or execute migrations during app import, Gunicorn worker startup, or Docker web-container startup.
5. **MUST** fail closed if the database identity, schema, revision chain, model metadata, detected SQL, backup state, or required approval cannot be verified. Never respond to an error by dropping/recreating a populated database.

## 2. Operation classification

| Class | Examples | Policy |
| --- | --- | --- |
| SAFE-CANDIDATE | `CREATE TABLE`, nullable `ADD COLUMN`, compatible nonunique index | Allow only after reviewing generated operations, current data and deployment impact. |
| REVIEW | `ALTER COLUMN TYPE`, `SET NOT NULL`, `UNIQUE`, `FOREIGN KEY`, data backfill, rename, nontransactional index operations | Explicit review, compatibility check, staging rehearsal; use backups when data/availability at risk. |
| DESTRUCTIVE | `DROP TABLE`, `DROP COLUMN`, `TRUNCATE`, bulk/unbounded `DELETE`, destructive `UPDATE`, `CASCADE`, `DROP SCHEMA`, `DROP DATABASE`, data-losing casts or table recreation | Block by default. Requires individually approved maintenance plan and verified recoverable backup. |
| UNKNOWN | raw/dynamic SQL, stored procedures, opaque `op.execute()`, unexpected schema diff | Fail closed until manually reviewed. |

**Important:** `alembic upgrade` can delete data; simply disabling `downgrade` does not protect it. `create_all()` normally only creates missing tables, whereas `drop_all()` drops them. Renames are **not** reliably detected by autogenerate: a rename may appear as `ADD + DROP`; replace it with explicit rename operations after review.

A successful backup must **not** automatically authorize destructive migrations. Removal of a deprecated table/column should normally use an **expand → backfill/migrate → switch readers/writers → verify → separately approved contract** sequence.

## 3. Protect model metadata and autogeneration

- **MUST** use the intended SQLAlchemy `DeclarativeBase`/metadata; ensure every managed model is imported before `target_metadata` is evaluated. If there are multiple metadata collections, enumerate them explicitly and check for duplicate keys.
- **MUST** compare the discovered managed tables with an independently maintained versioned schema manifest/expected-table baseline. A missing model import must abort migration generation; do **not** infer that a missing table should be dropped.
- **MUST** verify current database name, host, port, selected schema/search_path, environment identifier and Alembic revision. Refuse unexpected targets.
- **MUST** review `alembic revision --autogenerate` output. Add an `env.py` `process_revision_directives` guard that recursively rejects `DropTableOp` and `DropColumnOp`, including nested `OpContainer` operations. Additional risky operations need policy checks.
- **MUST** perform a separate execution-time audit. Generation-time hooks do **not** protect manually edited migration files, previously generated files, raw SQL or dynamically executed SQL.
- **SHOULD** use `alembic check` on a correctly provisioned test database to detect unapplied metadata changes. This is **not** a substitute for destructive-operation review, SQL inspection, or database-identity checks.
- **MUST** stop on multiple Alembic heads until migration ownership resolves the issue. `alembic heads` needs an explicit count assertion in CI; listing heads alone is not a failing test.

## 4. Multi-agent ownership and Git coordination

| Actor / scope | ORM changes | Generate revision | Upgrade shared database |
| --- | --- | --- | --- |
| Feature Agent, own worktree and isolated DB | Yes | Draft only | No |
| Migration Owner, integration branch | Yes | Sole owner of finalized migration | Through controlled runner only |
| CI/CD staging | No | Validate committed files | Serialized, approved job |
| Production deployer | No | Never generate migrations in production | Dedicated, authorized, serialized job |

- **MUST** use isolated Git branches/worktrees for concurrent Agents. Feature Agents MAY edit ORM models and SHOULD report a concise schema-change summary (tables, columns, constraints, indexes, backfills, potential data loss).
- **MUST** designate one Migration Owner per integration cycle. Only this owner finalizes `alembic/versions/*` after combining the full model metadata. Feature Agents MUST NOT independently run migrations against a shared database.
- **MUST** serialize commits that modify migration files, and forbid changes to migration files already applied in any shared environment.
- **MUST** verify that the single migration head builds a valid revision chain from the supported baseline and upgrades a fresh isolated DB and an upgrade-path fixture. Integrate/rebase before final autogeneration.
- **MUST NOT** resolve multi-head conflicts by rewriting deployed `down_revision` values, deleting historic versions, using `stamp head` without a documented reconciliation, or resetting the database. Alembic `merge` is possible after inspecting both branches and validating a deployed upgrade path; merge revisions do not themselves resolve conflicting schema operations.
- **SHOULD** protect migration paths via CODEOWNERS / required PR reviews and checks (where repository capabilities allow). Branch rules, not AGENTS.md alone, must enforce reviewers and CI.

## 5. Single controlled migration entry point

All persistent shared-environment upgrades **MUST** run through one maintained wrapper (recommended `python scripts/db_migrate.py upgrade`) or a single CI/CD migration job; no ad hoc web-worker `alembic upgrade head`.

Required pipeline:

1. Verify explicit environment and allowlisted DB fingerprint; forbid accidental production access using developer credentials.
2. Establish exclusive **PostgreSQL session-level advisory lock** on a dedicated connection and hold that *same session* throughout validation and Alembic execution. Abort if busy. Alembic `env.py` must reuse the supplied connection (e.g. via `Config.attributes["connection"]`), not open an uncoordinated one.
3. Inspect pending revisions, ensure single head and expected history, check metadata completeness, review generated SQL/operations, classify effects. Unknown SQL is blocked pending approval.
4. For destructive/data-risky changes, demand explicit approval, a successful off-host backup, and documented recovery validation; rehearsal in isolated staging is mandatory.
5. Execute once, with appropriate transactions/timeouts and explicit handling of PostgreSQL operations that cannot run in a transaction.
6. Validate post-migration schema, revision, crucial row counts/integrity, application compatibility and record audit metadata (who/agent, branch, commit SHA, revision, DB fingerprint, backup ID, approval ID, timestamps, outcome).
7. On failure: halt, preserve state/logs, assess transaction rollback and restore/recovery plan. Never auto-reset or auto-stamp.

**Lock caveat:** advisory locks are cooperative and only serialize clients that use the same lock key/protocol. Database access control must prevent other accounts bypassing this wrapper. Prefer one well-defined lock key per *database* and avoid transaction-pooling proxies that break session affinity.

## 6. PostgreSQL role separation

- `app_runtime`: only necessary DML/sequence access; no schema ownership or DDL privileges.
- `app_developer`: nonproduction DML as approved; no DDL on shared environments.
- `app_migrator`: narrowly scoped schema ownership / DDL; credentials only in the controlled migration job, not application environment.
- `app_backup`: permissions sufficient for the chosen backup procedure; not DDL.

Review PostgreSQL object **ownership**, role inheritance, `CREATE` on schemas and default privileges. Merely issuing `REVOKE CREATE` does not remove all owner powers. Credentials and backups must not be committed to Git.

## 7. Backup, restore and rollback policy

- **MUST** maintain verified off-host backups for all persistent environments and take an appropriate restore point before destructive or data-loss-risk migrations; production SHOULD additionally use physical base backups plus WAL archiving / PITR as required by RPO/RTO.
- `pg_dump -Fc` can provide a portable logical backup, but its existence alone does not prove recovery. Verify exit status, manifest/checksum, retention, scope (roles/extensions/large objects as applicable) and **test restoration to an isolated instance**.
- **MUST** document the migration's restore procedure and business-write handling; a logical dump may not include writes made after backup. If zero data loss is required, coordinate write downtime or use an appropriately verified PITR strategy.
- **MUST NOT** assume any failure is fully rolled back or that `downgrade` recovers deleted rows.
- **MUST** treat `DROP DATABASE` / volumes and administrator-level database replacement as outside ordinary migration scope.

## 8. CI test matrix and acceptance checklist

| Check | Required result |
| --- | --- |
| All managed ORM modules loaded, schema manifest matches expectations | Pass, or abort |
| Expected database identity / schema scope | Match, or abort |
| Alembic head count and ancestor chain | Exactly one supported head, no invalid refs |
| No unexpected `DropTableOp` / `DropColumnOp` or unsafe raw SQL | Block automatically |
| Required approvals/backups for dangerous operations | Present, verified, otherwise abort |
| Fresh isolated DB `upgrade head` | Pass |
| Existing schema upgrade fixture `upgrade head` | Pass, data preserved |
| `alembic check` against migrated test DB | Pass |
| Concurrent migrator attempt | Only one succeeds in acquiring lock |
| Migration failure injection | No automatic drop/recreate/stamp; evidence retained |
| Runtime DB role attempts DDL | Permission denied |
| Disaster-recovery test (scheduled) | Restore is demonstrably successful |

## 9. Environments, baseline and migration history

- Isolated disposable Agent databases MAY be recreated **only when explicitly labeled disposable, with no shared or valuable data**.
- Shared dev/staging/production databases MUST never be implicitly reset, including on tests, `docker compose down -v`, application boot, or schema mismatch.
- Current deployed migration revisions are immutable. Many small revisions are acceptable and generally preferable to history rewriting.
- History squashing/new baseline is allowed **only** as a separately planned compatibility transition that retains a correct upgrade path for every supported deployed environment. `alembic stamp` changes the version marker only; it does not build or repair schema objects.

## 10. Implementation plan (not yet applied)

- [ ] P0: Remove all implicit DDL from app startup / entrypoints and deployment scripts.
- [ ] P0: Inventory PostgreSQL DDL privileges; isolate runtime and migrator roles.
- [ ] P0: Add autogenerate destructive-op guard and metadata completeness/schema-manifest validation.
- [ ] P0: Implement controlled migrator with DB fingerprint, single-head assertion, shared-session advisory lock and fail-closed policy.
- [ ] P0: Add mandatory review, backup/restore verification and deployment approval gate for destructive/unknown operations.
- [ ] P1: Add CI tests for fresh/upgraded schema, concurrent migrations, missing model imports, destructive SQL and failure behavior.
- [ ] P1: Add PR ownership / protected branch controls for `alembic/versions/**`.
- [ ] P1: Establish routine restore drills and optional PostgreSQL PITR for important deployments.

## 11. Incident response: tables or database accidentally removed

1. Stop writers and all migrations immediately; prevent automated reinitialization.
2. Preserve existing PostgreSQL instance, volumes, logs, WAL and backups. Avoid overwrite or restarting destructive deployment automation.
3. Compare applied migrations, `alembic_version` where available, `env.py`, generated `drop_table()` and raw SQL, `drop_all()`, `DROP DATABASE`, `docker compose down -v` and external scripts.
4. Restore into a **new isolated instance** using the latest validated backup or suitable PITR; verify schema and data before cutover.
5. Record root cause and introduce regression tests for the identified failure route.

## References

- [Alembic autogenerate](https://alembic.sqlalchemy.org/en/latest/autogenerate.html)
- [Alembic cookbook: programmatic API and shared connection](https://alembic.sqlalchemy.org/en/latest/cookbook.html)
- [PostgreSQL advisory locks](https://www.postgresql.org/docs/16/explicit-locking.html#ADVISORY-LOCKS)
- [PostgreSQL pg_dump](https://www.postgresql.org/docs/16/app-pgdump.html)
- [PostgreSQL continuous archiving and PITR](https://www.postgresql.org/docs/16/continuous-archiving.html)

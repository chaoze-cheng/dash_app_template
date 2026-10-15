# Repository instructions for Codex Agents

## Goal
Create a local-only OpenLDAP development fixture with 10 users and 3 groups.

## Scope
- Do not connect to, query, or modify any real LDAP/AD server.
- Do not open LDAP/UI ports on 0.0.0.0.
- Do not commit .env or production secrets.
- Do not use Docker-wide destructive cleanup commands.
- Always treat this as development-only; TLS is intentionally disabled.

## Required outputs
- compose.yaml, .env.example, bootstrap/50-seed.ldif
- scripts/smoke-test.sh, scripts/reset.sh
- tests/requirements.txt, tests/test_ldap.py
- README.md with setup/troubleshooting/verification

## Run checks
1. docker compose config --quiet
2. docker compose up -d ldap
3. ./scripts/smoke-test.sh
4. pytest -q tests/ (when Python tooling is installed)
5. docker compose --profile ui up -d and verify UI manually if possible

## Done criteria
- 10 named users bind successfully; bad passwords fail.
- 3 groups have exact memberships; two users have no groups.
- Data survive restart and reset is guarded.
- No unintended volume deletion, no real LDAP access.
- Document all tests actually run and any blocked checks.

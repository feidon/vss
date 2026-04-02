## Why

The in-memory repository implementations currently serve double duty: they are the default production persistence layer (when `DB` env var is not set) and the test fixtures for application-level tests. This couples production startup to test infrastructure and means the production app can silently run without a real database. In-memory repos should exist solely as test doubles — production must always use PostgreSQL.

## What Changes

- **BREAKING**: Remove the in-memory fallback from `api/dependencies.py`. Production always requires `DB=postgres` (or equivalent configuration).
- Move in-memory repo usage exclusively into test fixtures (`tests/conftest.py` or per-test-module conftest files).
- Remove the `if os.getenv("DB") == "postgres"` branch in `api/dependencies.py` — the DI container always wires PostgreSQL repos.
- Simplify `main.py` lifespan: always initialize the database connection on startup.
- Keep `infra/memory/` module intact — it remains the test-double implementation of domain repository interfaces.

## Non-goals

- Removing the `infra/memory/` module entirely — it is still valuable for fast unit/application tests.
- Changing domain repository interfaces or PostgreSQL implementations.
- Migrating seed data loading — `infra/seed.py` continues to be used for both test fixtures and DB seeding.

## Capabilities

### New Capabilities

- `test-only-di`: Restructure DI wiring so in-memory repos are only injected via test fixture overrides, never in production startup.

### Modified Capabilities

- `postgres-repositories`: Production DI now unconditionally uses PostgreSQL repos (no fallback).
- `database-seeding`: Seed data loading in production moves from in-memory initialization to DB seeding only.

## Impact

- **`api/dependencies.py`**: Major rewrite — remove in-memory singleton creation and env-var branching; always return Postgres repos.
- **`main.py`**: Lifespan simplified — always connect to PostgreSQL, no conditional logic.
- **`tests/`**: Application-level tests (`tests/application/`) need conftest fixtures that provide in-memory repos. API tests already use PostgreSQL overrides and are unaffected.
- **Deployment**: `DB=postgres` (or direct database URL config) becomes mandatory. Running without a database is no longer possible.

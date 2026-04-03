# Alembic Migration System

**Date:** 2026-04-03
**Status:** Approved

## Problem

Database seeding runs on every app startup via `seed_database()` in the FastAPI lifespan. The seed IDs are generated with `uuid7()` at module import time, producing different UUIDs on each restart. Since `ON CONFLICT DO NOTHING` matches by ID, duplicate rows accumulate across restarts. The TODO "seeding need to check if already done" captures this.

Beyond seeding, schema creation uses `metadata.create_all()` directly — there's no migration history, making schema evolution difficult.

## Solution

Replace `metadata.create_all()` and `seed_database()` with Alembic migrations. Both DDL and DML live in versioned migration files tracked by Alembic's `alembic_version` table. Each migration runs exactly once.

## Prerequisites

### Deterministic Seed IDs

Replace all `uuid7()` calls in `infra/seed.py` with `uuid5()` using a fixed namespace. This ensures:
- Seed IDs are identical across processes, environments, and restarts
- The migration inserts the same IDs that tests reference via `BLOCK_ID_BY_NAME`, `PLATFORM_ID_BY_NAME`, etc.
- API tests importing these constants get IDs matching the seeded database

```python
from uuid import UUID, uuid5

_NS = UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")  # fixed namespace

YARD_ID = uuid5(_NS, "Y")
PLATFORM_ID_BY_NAME = {name: uuid5(_NS, name) for name in ["P1A", "P1B", ...]}
BLOCK_ID_BY_NAME = {f"B{i}": uuid5(_NS, f"B{i}") for i in range(1, 15)}
```

### Sync PostgreSQL Driver for Production

Alembic runs migrations synchronously. The production `DATABASE_URL` uses `asyncpg`, which Alembic cannot use directly. Add `psycopg[binary]` to **production** dependencies in `pyproject.toml` (currently dev-only). The `env.py` will translate the URL from `postgresql+asyncpg://` to `postgresql+psycopg://` at runtime.

## Design

### Migration Files

Create `backend/infra/postgres/alembic/versions/` directory with two migration files:

1. **`001_create_schema.py`** — Creates all 7 tables (stations, platforms, blocks, vehicles, services, node_connections, node_layouts) using `op.create_table()` matching `tables.py` definitions. The `upgrade()` drops existing tables first (`op.drop_table(if_exists=True)`) in reverse FK order for clean slate. The `downgrade()` drops tables in reverse FK dependency order: services, node_layouts, node_connections, vehicles, blocks, platforms, stations.

2. **`002_seed_data.py`** — Inserts all seed data (stations, platforms, blocks, vehicles, connections, node layouts). Imports data definitions from `infra/seed.py` (now deterministic) and uses `op.execute()` with bulk insert. The `downgrade()` truncates all seeded tables (excluding services).

### env.py Configuration

Update `infra/postgres/alembic/env.py`:
- Set `target_metadata` to `metadata` from `infra.postgres.tables`
- Override the URL from `DATABASE_URL` env var, translating async to sync driver:
  ```python
  import os
  url = os.environ.get("DATABASE_URL", "").replace("+asyncpg", "+psycopg")
  if url:
      config.set_main_option("sqlalchemy.url", url)
  ```
- Keep synchronous `engine_from_config` (Alembic's default pattern)

### Startup Changes

**`main.py` lifespan:**
- Remove `metadata.create_all()` call
- Remove `seed_database()` call
- Lifespan becomes empty (just `yield`) or removed entirely

**Docker entrypoint:**
- Change Dockerfile CMD to run `alembic upgrade head` before uvicorn:
  ```dockerfile
  CMD ["/bin/sh", "-c", ".venv/bin/alembic upgrade head && .venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000"]
  ```

Note: Alembic migrations run inside a transaction by default on PostgreSQL. If a migration fails partway, the transaction rolls back and the container restarts cleanly (`restart: unless-stopped`).

### File Changes

| File | Action |
|------|--------|
| `infra/seed.py` | Replace `uuid7()` with deterministic `uuid5()` |
| `pyproject.toml` | Move `psycopg[binary]` from dev to production dependencies |
| `infra/postgres/alembic/env.py` | Configure `target_metadata`, sync engine, env var URL override |
| `infra/postgres/alembic/versions/` | New directory |
| `infra/postgres/alembic/versions/001_create_schema.py` | New — DDL for all 7 tables |
| `infra/postgres/alembic/versions/002_seed_data.py` | New — DML for all seed data |
| `main.py` | Remove `metadata.create_all()` and `seed_database()` from lifespan |
| `Dockerfile` | Add `alembic upgrade head` before uvicorn |
| `infra/postgres/seed.py` | Delete (insert logic moves to migration) |
| `tests/infra/test_postgres_seed.py` | Delete — seed function no longer exists |
| `tests/infra/test_seed.py` | Keep — may need minor updates if ID assertions change |
| `alembic.ini` | Keep as-is (env.py overrides URL at runtime) |

### API Test Fixture Replacement

The current `tests/api/conftest.py` calls `seed_database(session)` from `infra/postgres/seed.py`. Since that file is deleted, replace with a test-only seed helper:

Create `tests/helpers/seed.py` that replicates the insert logic using `infra/seed.py` data definitions + SQLAlchemy Core inserts (same pattern as the deleted `seed_database()`). The `tests/api/conftest.py` imports from `tests/helpers/seed.py` instead.

This keeps the test seeding separate from the migration and avoids polluting production code with test-only functions.

### Existing Data Handling

For existing databases with duplicated seed data: the first migration (`001_create_schema`) drops and recreates tables (clean slate). This is acceptable since this is a dev/demo project. User-created services are lost on first migration — acknowledged.

### What Stays the Same

- `infra/postgres/tables.py` — SQLAlchemy Core table definitions remain (used by repositories and as `target_metadata` for Alembic autogenerate)
- `infra/seed.py` — data definition functions remain (now with deterministic IDs), used by migration and test fixtures
- Domain models, application layer, API layer — untouched
- Test fixtures — still use `metadata.create_all()` directly (tests don't run Alembic)
- `docker compose up` workflow — still just works (migration runs automatically in entrypoint)

### Local Development

For local development (without Docker):
- `cd backend && uv run alembic upgrade head` before starting uvicorn
- Test fixtures continue using `metadata.create_all()` for test DB setup

## Test Impact

- **Test fixtures** (`tests/conftest.py`): Keep using `metadata.create_all()` for test DB setup — tests don't go through Alembic
- **API test fixtures** (`tests/api/conftest.py`): Switch from `seed_database()` to new `tests/helpers/seed.py`
- **`test_postgres_seed.py`**: Delete — the `seed_database()` function no longer exists
- **`test_seed.py`**: Keep — update ID assertions if needed after uuid7 -> uuid5 change
- **API test files** importing seed constants (`BLOCK_ID_BY_NAME`, `PLATFORM_ID_BY_NAME`, `VEHICLE_ID_BY_NAME`, `YARD_ID`): No changes needed — these import from `infra/seed.py` which now produces deterministic IDs matching what the test seed helper inserts
- Add new `tests/infra/test_alembic_migrations.py`: verify `alembic upgrade head` + `alembic downgrade base` round-trips cleanly against the test database using `alembic.config.Config` + `alembic.command`

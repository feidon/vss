# Alembic Migration System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace `metadata.create_all()` and `seed_database()` with Alembic migrations so DDL and DML are versioned and run exactly once.

**Architecture:** Two Alembic migration files (schema via autogenerate + seed) replace the current startup logic. Docker entrypoint runs `alembic upgrade head` before uvicorn. Test fixtures keep using `metadata.create_all()` with a new seed helper.

**Tech Stack:** Alembic, SQLAlchemy Core, psycopg, PostgreSQL 17

**Spec:** `docs/superpowers/specs/2026-04-03-alembic-migrations-design.md`

---

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `backend/pyproject.toml` | Modify | Move psycopg to production deps |
| `backend/infra/postgres/alembic/env.py` | Modify | Configure target_metadata, sync engine, DATABASE_URL override |
| `backend/infra/postgres/alembic/versions/<rev>_create_schema.py` | Create (autogenerate) | DDL for all 7 tables |
| `backend/infra/postgres/alembic/versions/002_seed_data.py` | Create | DML for all seed data |
| `backend/main.py` | Modify | Remove create_all and seed_database from lifespan |
| `backend/Dockerfile` | Modify | Add alembic upgrade head before uvicorn |
| `backend/infra/postgres/seed.py` | Delete | Insert logic moves to migration |
| `backend/tests/helpers/__init__.py` | Create | Package init |
| `backend/tests/helpers/seed.py` | Create | Test-only seed insert helper |
| `backend/tests/api/conftest.py` | Modify | Use tests/helpers/seed instead of infra/postgres/seed |
| `backend/tests/infra/test_postgres_seed.py` | Delete | seed_database() no longer exists |
| `backend/tests/infra/test_alembic_migrations.py` | Create | Alembic upgrade/downgrade round-trip test |

---

### Task 1: Move psycopg to Production Dependencies

**Files:**
- Modify: `backend/pyproject.toml:7-13,16-25`

- [ ] **Step 1: Add psycopg[binary] to production dependencies and remove from dev**

In `pyproject.toml`, add `"psycopg[binary]>=3.3.3"` to the `dependencies` list and remove both `"psycopg-binary>=3.3.3"` and `"psycopg[binary]>=3.3.3"` from the `dev` dependency group.

The dependencies section should become:
```toml
dependencies = [
    "alembic>=1.18.4",
    "asyncpg>=0.31.0",
    "fastapi>=0.135.2",
    "psycopg[binary]>=3.3.3",
    "sqlalchemy>=2.0.48",
    "uvicorn>=0.42.0",
]
```

The dev group should become:
```toml
[dependency-groups]
dev = [
    "httpx>=0.28.1",
    "import-linter>=2.1",
    "pre-commit>=4.5.1",
    "pytest>=9.0.2",
    "pytest-asyncio>=1.3.0",
    "ruff>=0.15.8",
]
```

- [ ] **Step 2: Sync dependencies**

Run: `cd /home/feidon/Documents/vss/backend && uv sync`
Expected: Lock file updated, no errors

- [ ] **Step 3: Verify import works**

Run: `cd /home/feidon/Documents/vss/backend && uv run python -c "import psycopg; print('OK')"`
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
cd /home/feidon/Documents/vss && git add backend/pyproject.toml backend/uv.lock
git commit -m "chore: move psycopg to production dependencies for Alembic"
```

---

### Task 2: Configure Alembic env.py

**Files:**
- Modify: `backend/infra/postgres/alembic/env.py`

- [ ] **Step 1: Rewrite env.py with proper configuration**

Replace the entire contents of `backend/infra/postgres/alembic/env.py` with:

```python
"""Alembic environment configuration.

Reads DATABASE_URL from the environment and translates the async driver
(asyncpg) to the sync driver (psycopg) that Alembic requires.
"""

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from infra.postgres.tables import metadata

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = metadata

# Override URL from environment, converting async driver to sync.
_db_url = os.environ.get("DATABASE_URL", "")
if _db_url:
    config.set_main_option(
        "sqlalchemy.url", _db_url.replace("+asyncpg", "+psycopg")
    )


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

- [ ] **Step 2: Verify Alembic can load the config**

Run: `cd /home/feidon/Documents/vss/backend && DATABASE_URL=postgresql+asyncpg://vss:vss@localhost:5432/vss uv run alembic heads`
Expected: No errors (may show empty heads since no migrations yet)

- [ ] **Step 3: Commit**

```bash
cd /home/feidon/Documents/vss && git add backend/infra/postgres/alembic/env.py
git commit -m "feat: configure Alembic env.py with target metadata and DATABASE_URL"
```

---

### Task 3: Autogenerate Schema Migration (001)

**Files:**
- Create: `backend/infra/postgres/alembic/versions/<rev>_create_schema.py` (autogenerated)

- [ ] **Step 1: Create the versions directory**

Run: `mkdir -p /home/feidon/Documents/vss/backend/infra/postgres/alembic/versions`

- [ ] **Step 2: Ensure a clean database for autogenerate**

Alembic autogenerate compares `target_metadata` against the actual database. The database must be empty (no existing tables) so autogenerate produces CREATE statements for all 7 tables. Drop existing tables if needed:

Run: `cd /home/feidon/Documents/vss/backend && DATABASE_URL=postgresql+asyncpg://vss:vss@localhost:5432/vss uv run python -c "
from sqlalchemy import create_engine, text
engine = create_engine('postgresql+psycopg://vss:vss@localhost:5432/vss')
with engine.begin() as conn:
    for t in ['services','node_layouts','node_connections','vehicles','blocks','platforms','stations']:
        conn.execute(text(f'DROP TABLE IF EXISTS {t} CASCADE'))
engine.dispose()
print('Tables dropped')
"`
Expected: `Tables dropped`

- [ ] **Step 3: Autogenerate the schema migration**

Run: `cd /home/feidon/Documents/vss/backend && DATABASE_URL=postgresql+asyncpg://vss:vss@localhost:5432/vss uv run alembic revision --autogenerate -m "create schema"`
Expected: Creates a migration file in `versions/` with all 7 `op.create_table()` calls

- [ ] **Step 4: Review the generated migration**

Open the generated file and verify it contains `create_table` for all 7 tables: stations, platforms, blocks, vehicles, services, node_connections, node_layouts. Also verify the `downgrade()` contains matching `drop_table` calls in reverse FK order. Fix ordering if needed (services before platforms before stations, etc.).

- [ ] **Step 5: Verify Alembic sees the migration**

Run: `cd /home/feidon/Documents/vss/backend && DATABASE_URL=postgresql+asyncpg://vss:vss@localhost:5432/vss uv run alembic heads`
Expected: Shows the generated revision as the head

- [ ] **Step 6: Commit**

```bash
cd /home/feidon/Documents/vss && git add backend/infra/postgres/alembic/versions/
git commit -m "feat: add Alembic migration for schema creation (autogenerated)"
```

---

### Task 4: Create Seed Data Migration (002)

**Files:**
- Create: `backend/infra/postgres/alembic/versions/002_seed_data.py`

- [ ] **Step 1: Get the revision ID from the autogenerated schema migration**

Run: `cd /home/feidon/Documents/vss/backend && DATABASE_URL=postgresql+asyncpg://vss:vss@localhost:5432/vss uv run alembic heads`

Note the revision ID (e.g., `a1b2c3d4e5f6`) — the seed migration's `down_revision` must point to it.

- [ ] **Step 2: Create the seed data migration file**

Create `backend/infra/postgres/alembic/versions/002_seed_data.py` (replace `<schema_rev>` with the actual revision ID from Step 1):

```python
"""Seed reference data.

Revision ID: 002
Revises: <schema_rev>
Create Date: 2026-04-03
"""

from typing import Sequence, Union

from alembic import op
from infra.postgres.tables import (
    blocks_table,
    node_connections_table,
    node_layouts_table,
    platforms_table,
    stations_table,
    vehicles_table,
)
from infra.seed import (
    create_blocks,
    create_connections,
    create_node_layouts,
    create_stations,
    create_vehicles,
)
from sqlalchemy import text

revision: str = "002"
down_revision: Union[str, Sequence[str], None] = "<schema_rev>"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    stations = create_stations()
    conn.execute(
        stations_table.insert(),
        [{"id": s.id, "name": s.name, "is_yard": s.is_yard} for s in stations],
    )

    platform_rows = [
        {"id": p.id, "name": p.name, "station_id": s.id}
        for s in stations
        for p in s.platforms
    ]
    if platform_rows:
        conn.execute(platforms_table.insert(), platform_rows)

    blocks = create_blocks()
    conn.execute(
        blocks_table.insert(),
        [
            {
                "id": b.id,
                "name": b.name,
                "group": b.group,
                "traversal_time_seconds": b.traversal_time_seconds,
            }
            for b in blocks
        ],
    )

    vehicles = create_vehicles()
    conn.execute(
        vehicles_table.insert(),
        [{"id": v.id, "name": v.name} for v in vehicles],
    )

    connections = create_connections()
    conn.execute(
        node_connections_table.insert(),
        [{"from_id": c.from_id, "to_id": c.to_id} for c in connections],
    )

    layouts = create_node_layouts()
    conn.execute(
        node_layouts_table.insert(),
        [{"node_id": nid, "x": x, "y": y} for nid, (x, y) in layouts.items()],
    )


def downgrade() -> None:
    conn = op.get_bind()
    for table in [
        "node_layouts",
        "node_connections",
        "vehicles",
        "blocks",
        "platforms",
        "stations",
    ]:
        conn.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
```

- [ ] **Step 3: Verify Alembic sees both migrations in order**

Run: `cd /home/feidon/Documents/vss/backend && DATABASE_URL=postgresql+asyncpg://vss:vss@localhost:5432/vss uv run alembic history`
Expected: Shows `<schema_rev> -> 002 (head)`

- [ ] **Step 4: Commit**

```bash
cd /home/feidon/Documents/vss && git add backend/infra/postgres/alembic/versions/002_seed_data.py
git commit -m "feat: add Alembic migration 002 for seed data"
```

---

### Task 5: Create Test Seed Helper and Update API Fixtures

**Files:**
- Create: `backend/tests/helpers/__init__.py`
- Create: `backend/tests/helpers/seed.py`
- Modify: `backend/tests/api/conftest.py:15,37`

- [ ] **Step 1: Create `tests/helpers/__init__.py`**

Create an empty `backend/tests/helpers/__init__.py`.

- [ ] **Step 2: Create `tests/helpers/seed.py`**

This replicates the insert logic from the deleted `infra/postgres/seed.py`, using the same data definitions from `infra/seed.py`:

```python
"""Test-only seed helper.

Replicates the seed insert logic for use in test fixtures.
Production seeding is handled by Alembic migration 002.
"""

from __future__ import annotations

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from infra.postgres.tables import (
    blocks_table,
    node_connections_table,
    node_layouts_table,
    platforms_table,
    stations_table,
    vehicles_table,
)
from infra.seed import (
    create_blocks,
    create_connections,
    create_node_layouts,
    create_stations,
    create_vehicles,
)


async def seed_test_database(session: AsyncSession) -> None:
    """Insert all reference data for tests. Idempotent via ON CONFLICT DO NOTHING."""
    stations = create_stations()
    blocks = create_blocks()
    vehicles = create_vehicles()
    connections = create_connections()

    await session.execute(
        insert(stations_table)
        .values([{"id": s.id, "name": s.name, "is_yard": s.is_yard} for s in stations])
        .on_conflict_do_nothing(index_elements=["id"])
    )

    platform_rows = [
        {"id": p.id, "name": p.name, "station_id": s.id}
        for s in stations
        for p in s.platforms
    ]
    if platform_rows:
        await session.execute(
            insert(platforms_table)
            .values(platform_rows)
            .on_conflict_do_nothing(index_elements=["id"])
        )

    await session.execute(
        insert(blocks_table)
        .values(
            [
                {
                    "id": b.id,
                    "name": b.name,
                    "group": b.group,
                    "traversal_time_seconds": b.traversal_time_seconds,
                }
                for b in blocks
            ]
        )
        .on_conflict_do_nothing(index_elements=["id"])
    )

    await session.execute(
        insert(vehicles_table)
        .values([{"id": v.id, "name": v.name} for v in vehicles])
        .on_conflict_do_nothing(index_elements=["id"])
    )

    await session.execute(
        insert(node_connections_table)
        .values([{"from_id": c.from_id, "to_id": c.to_id} for c in connections])
        .on_conflict_do_nothing()
    )

    layouts = create_node_layouts()
    await session.execute(
        insert(node_layouts_table)
        .values([{"node_id": nid, "x": x, "y": y} for nid, (x, y) in layouts.items()])
        .on_conflict_do_nothing(index_elements=["node_id"])
    )

    await session.commit()
```

- [ ] **Step 3: Update `tests/api/conftest.py` to use the new helper**

Replace the import on line 15:
```python
# Old:
from infra.postgres.seed import seed_database
# New:
from tests.helpers.seed import seed_test_database
```

Replace the call on line 37:
```python
# Old:
await seed_database(session)
# New:
await seed_test_database(session)
```

- [ ] **Step 4: Run API tests to verify fixtures work**

Run: `cd /home/feidon/Documents/vss/backend && uv run pytest tests/api/ -v -m postgres`
Expected: All API tests PASS

- [ ] **Step 5: Commit**

```bash
cd /home/feidon/Documents/vss && git add backend/tests/helpers/ backend/tests/api/conftest.py
git commit -m "test: add seed helper for test fixtures"
```

---

### Task 6: Remove Old Startup Logic and Delete infra/postgres/seed.py

**Files:**
- Modify: `backend/main.py:1-27`
- Delete: `backend/infra/postgres/seed.py`
- Delete: `backend/tests/infra/test_postgres_seed.py`

- [ ] **Step 1: Update main.py lifespan**

Replace the lifespan function and remove unused imports. The new `main.py` top section:

```python
from contextlib import asynccontextmanager
from pathlib import Path

from api.block.routes import router as block_router
from api.error_handler import domain_error_handler
from api.route.routes import router as route_router
from api.service.routes import router as service_router
from api.vehicle.routes import router as vehicle_router
from domain.error import DomainError
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
```

This removes imports of `seed_database`, `async_session`, `engine`, and `metadata`.

- [ ] **Step 2: Delete `infra/postgres/seed.py`**

Run: `rm /home/feidon/Documents/vss/backend/infra/postgres/seed.py`

- [ ] **Step 3: Delete `tests/infra/test_postgres_seed.py`**

Run: `rm /home/feidon/Documents/vss/backend/tests/infra/test_postgres_seed.py`

- [ ] **Step 4: Run unit tests to verify nothing references deleted files**

Run: `cd /home/feidon/Documents/vss/backend && uv run pytest -v`
Expected: All tests PASS (no import errors)

- [ ] **Step 5: Run import linter**

Run: `cd /home/feidon/Documents/vss/backend && uv run lint-imports`
Expected: All contracts PASS

- [ ] **Step 6: Commit**

```bash
cd /home/feidon/Documents/vss && git add backend/main.py && git rm backend/infra/postgres/seed.py backend/tests/infra/test_postgres_seed.py
git commit -m "refactor: remove metadata.create_all and seed_database from startup"
```

---

### Task 7: Update Dockerfile Entrypoint

**Files:**
- Modify: `backend/Dockerfile:21`

- [ ] **Step 1: Update Dockerfile CMD to run migrations before uvicorn**

Replace line 21 of `backend/Dockerfile`:

```dockerfile
CMD ["/bin/sh", "-c", ".venv/bin/alembic upgrade head && .venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000"]
```

- [ ] **Step 2: Commit**

```bash
cd /home/feidon/Documents/vss && git add backend/Dockerfile
git commit -m "feat: run Alembic migrations in Docker entrypoint"
```

---

### Task 8: Integration Test — Alembic Round-Trip

**Files:**
- Create: `backend/tests/infra/test_alembic_migrations.py`

- [ ] **Step 1: Write the round-trip test**

Create `backend/tests/infra/test_alembic_migrations.py`:

```python
"""Verify Alembic migrations upgrade and downgrade cleanly."""

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

from tests.pg_config import TEST_DATABASE_URL_SYNC

pytestmark = pytest.mark.postgres

ALEMBIC_INI = "alembic.ini"


def _alembic_config() -> Config:
    cfg = Config(ALEMBIC_INI)
    cfg.set_main_option("sqlalchemy.url", TEST_DATABASE_URL_SYNC)
    return cfg


@pytest.fixture(autouse=True)
def _clean_alembic():
    """Downgrade to base before and after each test."""
    cfg = _alembic_config()
    command.downgrade(cfg, "base")
    yield
    command.downgrade(cfg, "base")


class TestAlembicMigrations:
    def test_upgrade_to_head_creates_all_tables(self):
        cfg = _alembic_config()
        command.upgrade(cfg, "head")

        engine = create_engine(TEST_DATABASE_URL_SYNC)
        inspector = inspect(engine)
        table_names = set(inspector.get_table_names())
        engine.dispose()

        expected = {
            "stations",
            "platforms",
            "blocks",
            "vehicles",
            "services",
            "node_connections",
            "node_layouts",
            "alembic_version",
        }
        assert expected.issubset(table_names)

    def test_upgrade_seeds_data(self):
        cfg = _alembic_config()
        command.upgrade(cfg, "head")

        engine = create_engine(TEST_DATABASE_URL_SYNC)
        with engine.connect() as conn:
            stations = conn.execute(text("SELECT count(*) FROM stations")).scalar()
            blocks = conn.execute(text("SELECT count(*) FROM blocks")).scalar()
            vehicles = conn.execute(text("SELECT count(*) FROM vehicles")).scalar()
        engine.dispose()

        assert stations == 4
        assert blocks == 14
        assert vehicles == 3

    def test_downgrade_to_base_removes_tables(self):
        cfg = _alembic_config()
        command.upgrade(cfg, "head")
        command.downgrade(cfg, "base")

        engine = create_engine(TEST_DATABASE_URL_SYNC)
        inspector = inspect(engine)
        table_names = set(inspector.get_table_names())
        engine.dispose()

        schema_tables = {
            "stations",
            "platforms",
            "blocks",
            "vehicles",
            "services",
            "node_connections",
            "node_layouts",
        }
        assert schema_tables.isdisjoint(table_names)
```

- [ ] **Step 2: Run the Alembic integration test**

Run: `cd /home/feidon/Documents/vss/backend && uv run pytest tests/infra/test_alembic_migrations.py -v -m postgres`
Expected: All 3 tests PASS

- [ ] **Step 3: Run full test suite (unit + integration)**

Run: `cd /home/feidon/Documents/vss/backend && uv run pytest -v -m ''`
Expected: All tests PASS

- [ ] **Step 4: Commit**

```bash
cd /home/feidon/Documents/vss && git add backend/tests/infra/test_alembic_migrations.py
git commit -m "test: add Alembic upgrade/downgrade round-trip integration test"
```

---

### Task 9: Update README TODO List

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Remove the completed TODO item from README**

Remove the line `- [ ] seeding need to check if already done` from the Todo section.

- [ ] **Step 2: Commit**

```bash
cd /home/feidon/Documents/vss && git add README.md
git commit -m "docs: remove completed seeding TODO"
```

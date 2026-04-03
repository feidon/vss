# Testcontainers Postgres Migration Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace manual docker-compose postgres dependency with testcontainers so `pytest -m postgres` is fully self-contained — spins up its own container, tests, tears down.

**Architecture:** Session-scoped pytest fixture creates a `PostgresContainer(image="postgres:17")`. All test URLs are derived from the container's dynamic connection string. Alembic env.py is fixed to respect programmatic URL overrides. The `@classmethod` bug in `schemas.py` is fixed as a prerequisite.

**Tech Stack:** testcontainers[postgres], pytest, SQLAlchemy, alembic

---

### Task 0: Fix pre-existing `@classmethod` bug in `api/route/schemas.py`

**Files:**
- Modify: `api/route/schemas.py:18-20`

- [ ] **Step 1: Fix `to_route_stop` from `@classmethod` to instance method**

`api/route/schemas.py` — `to_route_stop` is declared as `@classmethod` but accesses instance data (`cls.stops`). Change to a regular method:

```python
# Before (broken):
@classmethod
def to_route_stop(cls) -> list[RouteStop]:
    return [RouteStop(node_id=s.node_id, dwell_time=s.dwell_time) for s in cls.stops]

# After (fixed):
def to_route_stop(self) -> list[RouteStop]:
    return [RouteStop(node_id=s.node_id, dwell_time=s.dwell_time) for s in self.stops]
```

- [ ] **Step 2: Run unit tests to verify no regressions**

Run: `uv run pytest tests/ -x -v`
Expected: all non-postgres tests pass

---

### Task 1: Add `testcontainers[postgres]` dependency

**Files:**
- Modify: `pyproject.toml` (dev dependencies)

- [ ] **Step 1: Add testcontainers to dev deps**

In `pyproject.toml`, add to the `[dependency-groups] dev` list:

```toml
"testcontainers[postgres]>=4.10.0",
```

- [ ] **Step 2: Sync dependencies**

Run: `uv sync`
Expected: installs testcontainers and its postgres extra

---

### Task 2: Rewrite `tests/pg_config.py` — container-driven URLs

**Files:**
- Modify: `tests/pg_config.py`

- [ ] **Step 1: Replace hardcoded URLs with container-derived URL holder**

Replace the entire file. URLs will be set at runtime by the session fixture in conftest.py. The module just holds mutable state that fixtures populate:

```python
"""Connection URLs for postgres integration tests.

Populated at runtime by the testcontainers session fixture in conftest.py.
"""

# Set by conftest._pg_container fixture
TEST_DATABASE_URL: str = ""
TEST_DATABASE_URL_SYNC: str = ""
```

No more `ADMIN_DATABASE_URL_SYNC` or `TEST_DATABASE_NAME` — the container provides everything.

---

### Task 3: Rewrite `tests/conftest.py` — testcontainers session fixture

**Files:**
- Modify: `tests/conftest.py`

- [ ] **Step 1: Replace the file with testcontainers-based fixtures**

```python
"""Shared fixtures for PostgreSQL integration tests.

Uses testcontainers to spin up a throwaway Postgres 17 container per session.
No external database required.
"""

from __future__ import annotations

from uuid import UUID

import pytest
import tests.pg_config as pg_config
from infra.postgres.tables import metadata, vehicles_table
from sqlalchemy import create_engine, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from testcontainers.postgres import PostgresContainer

_TABLE_NAMES = ", ".join(t.name for t in metadata.sorted_tables)


@pytest.fixture(scope="session")
def _pg_container():
    """Start a Postgres 17 container for the entire test session."""
    with PostgresContainer("postgres:17", driver="psycopg") as pg:
        sync_url = pg.get_connection_url()  # postgresql+psycopg://...
        async_url = sync_url.replace("+psycopg", "+asyncpg")

        # Populate the shared config so other modules can read URLs
        pg_config.TEST_DATABASE_URL = async_url
        pg_config.TEST_DATABASE_URL_SYNC = sync_url

        yield pg


@pytest.fixture(scope="session")
def _pg_tables(_pg_container):
    """Create all tables once per test session."""
    sync_engine = create_engine(pg_config.TEST_DATABASE_URL_SYNC)
    metadata.create_all(sync_engine)
    sync_engine.dispose()
    yield


@pytest.fixture
async def pg_session(_pg_tables):
    """Provide a clean database session for each test.

    Uses NullPool so connections aren't reused across event loops.
    Tables are truncated after each test.
    """
    engine = create_async_engine(pg_config.TEST_DATABASE_URL, poolclass=NullPool)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    async with engine.begin() as conn:
        await conn.execute(text(f"TRUNCATE TABLE {_TABLE_NAMES} CASCADE"))
    await engine.dispose()


async def insert_vehicle(
    session: AsyncSession, vehicle_id: UUID, name: str = "V1"
) -> None:
    """Insert a vehicle row (shared helper for FK setup)."""
    await session.execute(insert(vehicles_table).values(id=vehicle_id, name=name))
    await session.commit()
```

Key changes vs current:
- `_pg_container` (session): starts container, populates `pg_config` URLs
- `_pg_tables` depends on `_pg_container` instead of calling `_ensure_test_database`
- No `_ensure_test_database` / `_drop_test_database` — container handles lifecycle
- No teardown needed — container auto-removes, tables go with it

- [ ] **Step 2: Verify conftest imports resolve**

Run: `uv run python -c "import tests.conftest"`
Expected: no import errors

---

### Task 4: Update `tests/api/conftest.py` — use dynamic URLs

**Files:**
- Modify: `tests/api/conftest.py`

- [ ] **Step 1: Replace static import with dynamic pg_config read**

Change the import at the top:
```python
# Before:
from tests.pg_config import TEST_DATABASE_URL

# After:
import tests.pg_config as pg_config
```

And inside the `client` fixture, replace `TEST_DATABASE_URL` with `pg_config.TEST_DATABASE_URL`:

```python
@pytest.fixture
async def client(_pg_tables):
    engine = create_async_engine(pg_config.TEST_DATABASE_URL, poolclass=NullPool)
    # ... rest unchanged
```

---

### Task 5: Fix `alembic/env.py` — respect programmatic URL overrides

**Files:**
- Modify: `infra/postgres/alembic/env.py:24-27`

- [ ] **Step 1: Only apply `.env` override when URL is the default placeholder**

The problem: `load_dotenv()` loads `DATABASE_URL` from `.env`, which unconditionally overrides the URL that the test set via `cfg.set_main_option()`. Fix by checking if the URL has already been set programmatically:

```python
# Before:
_db_url = os.environ.get("DATABASE_URL", "")
if _db_url:
    config.set_main_option("sqlalchemy.url", _db_url.replace("+asyncpg", "+psycopg"))

# After:
_current_url = config.get_main_option("sqlalchemy.url", "")
_is_placeholder = not _current_url or _current_url == "driver://user:pass@localhost/dbname"
_db_url = os.environ.get("DATABASE_URL", "")
if _db_url and _is_placeholder:
    config.set_main_option("sqlalchemy.url", _db_url.replace("+asyncpg", "+psycopg"))
```

This preserves production behavior (`.env` still works when URL is the default from `alembic.ini`) but stops overriding test URLs.

---

### Task 6: Update alembic migration test to use testcontainers

**Files:**
- Modify: `tests/infra/test_alembic_migrations.py`

- [ ] **Step 1: Rewrite to use the container URL**

The migration test needs to point alembic at the testcontainer, not at hardcoded `vss_test`. It also needs to depend on `_pg_container` (not `_pg_tables`, since it manages its own schema via alembic):

```python
"""Verify Alembic migrations upgrade and downgrade cleanly."""

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

import tests.pg_config as pg_config

pytestmark = pytest.mark.postgres

ALEMBIC_INI = "alembic.ini"


def _alembic_config() -> Config:
    cfg = Config(ALEMBIC_INI)
    cfg.set_main_option("sqlalchemy.url", pg_config.TEST_DATABASE_URL_SYNC)
    return cfg


@pytest.fixture(autouse=True)
def _clean_alembic(_pg_container):
    """Downgrade to base before and after each test."""
    cfg = _alembic_config()
    command.downgrade(cfg, "base")
    yield
    command.downgrade(cfg, "base")


class TestAlembicMigrations:
    def test_upgrade_to_head_creates_all_tables(self):
        cfg = _alembic_config()
        command.upgrade(cfg, "head")

        engine = create_engine(pg_config.TEST_DATABASE_URL_SYNC)
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

        engine = create_engine(pg_config.TEST_DATABASE_URL_SYNC)
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

        engine = create_engine(pg_config.TEST_DATABASE_URL_SYNC)
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

Key change: `_clean_alembic` depends on `_pg_container` (not `_pg_tables`) so the container is up but tables are managed by alembic, not SQLAlchemy metadata.

---

### Task 7: Run all postgres tests end-to-end

- [ ] **Step 1: Run postgres tests**

Run: `uv run pytest -m postgres -v`
Expected: all tests pass, container starts and stops automatically

- [ ] **Step 2: Run all tests (unit + postgres)**

Run: `uv run pytest -m '' -v`
Expected: all tests pass

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "feat: replace manual postgres setup with testcontainers

Tests now spin up a throwaway Postgres 17 container per session.
No external docker-compose needed for pytest -m postgres."
```

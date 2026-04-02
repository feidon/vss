## Context

`api/dependencies.py` uses `os.getenv("DB") == "postgres"` to choose between PostgreSQL and in-memory repositories at module-import time. The in-memory branch creates singleton instances, populates them with seed data, and serves them for the lifetime of the process. This means the production app can run without a database — a convenience during early development that is now a liability since PostgreSQL repos and migrations are fully implemented.

Application-level tests (`tests/application/`) already construct in-memory repos directly in fixtures — they do not depend on the DI container's in-memory path. API tests override DI to use PostgreSQL. Only the production startup path still uses in-memory repos.

## Goals / Non-Goals

**Goals:**
- Production DI always wires PostgreSQL repositories — no silent in-memory fallback.
- Simplify `dependencies.py` by removing the env-var branch and all in-memory imports/initialization.
- Simplify `main.py` lifespan by always initializing the database.
- Keep `infra/memory/` intact as test infrastructure.

**Non-Goals:**
- Changing test structure — application tests already use in-memory repos directly.
- Modifying domain interfaces or PostgreSQL implementations.
- Removing `infra/seed.py` — still needed for DB seeding and test factories.

## Decisions

### D1: Remove env-var branching from `dependencies.py`

**Decision**: All `get_*_repo()` functions unconditionally return PostgreSQL repository instances, taking `AsyncSession` via FastAPI `Depends(get_session)`.

**Rationale**: The current `if/else` at module-import time means the dependency signatures differ between branches (Postgres providers accept `session`, in-memory providers don't). This is fragile and confusing. A single code path is simpler and prevents accidental in-memory production usage.

**Alternative considered**: Keep env-var switching but default to `postgres`. Rejected — adds complexity for a fallback mode that should never run in production.

### D2: Remove conditional from `main.py` lifespan

**Decision**: The lifespan always runs `metadata.create_all` and `seed_database`. The `if os.getenv("DB") == "postgres"` guard is removed.

**Rationale**: Since production always uses PostgreSQL, the lifespan should always initialize the database. Conditional logic was only needed because the in-memory path had no database to initialize.

### D3: Keep `infra/memory/` module unchanged

**Decision**: Do not move, rename, or delete in-memory repo files. They remain at `infra/memory/`.

**Rationale**: These are legitimate implementations of domain repository interfaces, used as test doubles. Moving them to `tests/` would break the hexagonal architecture convention (infra implements domain interfaces). Application tests already import them directly — no wiring change needed there.

**Alternative considered**: Move to `tests/helpers/`. Rejected — they implement domain ports and belong in the infra layer. The `infra/` directory is for all adapter implementations, not just production ones.

### D4: Remove unused in-memory imports from `dependencies.py`

**Decision**: Remove all `from infra.memory.*` and `from infra.seed import ...` lines from `dependencies.py` since they are no longer used there.

**Rationale**: Dead imports are confusing and may cause import-time side effects.

## Risks / Trade-offs

- **[Risk] Can't start app without PostgreSQL** → This is intentional. If developers need a quick-start without Docker, they must set up the database first. Documented in README.
- **[Risk] Seed data timing** → `seed_database` runs on every startup. The existing implementation uses upserts (ON CONFLICT), so this is idempotent and safe.
- **[Trade-off] Slightly slower dev startup** → Database connection adds ~100ms startup latency vs in-memory. Negligible in practice.

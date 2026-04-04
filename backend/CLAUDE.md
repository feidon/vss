# VSS Backend

## Tech Stack

- Python 3.14 + FastAPI
- PostgreSQL 17 (Docker)
- SQLAlchemy Core 2.0 + manual mapper (no ORM)
- Alembic for schema migrations
- asyncpg for async database access
- Package manager: uv
- Linting: Ruff (check + format), import-linter (architecture enforcement)

## Architecture

Hexagonal Architecture (Ports & Adapters) with DDD:

```
backend/
├── api/            # FastAPI routes, Pydantic schemas, DI container (inbound adapter)
├── application/    # App services, DTOs, orchestration (use cases)
├── domain/         # Entities, value objects, repository interfaces, domain services (core)
├── infra/postgres/ # PostgreSQL repos, Alembic migrations, seed data (outbound adapter)
└── tests/          # Mirrors source structure: domain/, application/, api/, infra/
    └── fakes/      # In-memory repository implementations (test doubles)
```

Dependency flow: `api → application → domain ← infra`

Enforced at CI time via `import-linter` contracts in `pyproject.toml`.

## Key Domain Services

- **ConflictDetectionService**: detects vehicle, block occupancy, interlocking, and battery conflicts (sweep-line + simulation)
- **RouteFinder**: BFS pathfinding to insert intermediate blocks between platform stops

Both are pure — no repository access, no I/O, no state.

## API Endpoints

All routes are under the `/api` prefix.

| Method | Path                       | Description                |
|--------|----------------------------|----------------------------|
| GET    | `/api/blocks`              | List all blocks            |
| PATCH  | `/api/blocks/{id}`         | Update traversal time      |
| POST   | `/api/services`            | Create service             |
| GET    | `/api/services`            | List services (with start_time, origin, destination) |
| GET    | `/api/services/{id}`       | Get service detail + graph |
| PATCH  | `/api/services/{id}/route` | Update service route       |
| DELETE | `/api/services/{id}`       | Delete service             |
| POST   | `/api/routes/validate`     | Validate route stops       |
| GET    | `/api/vehicles`            | List all vehicles          |

Route update returns 409 with conflict details when scheduling conflicts are detected.

### Validation Scope Split

- **`POST /api/routes/validate` (during editing):** Route connectivity + single-service battery only. No cross-service conflict checks — the route isn't final during editing.
- **`PATCH /api/services/{id}/route` (save):** Full cross-service conflict detection (vehicle, block, interlocking, battery) against all existing services.

## Running

PostgreSQL is always required — the app will not start without a database connection.

```bash
uv sync
uv run uvicorn main:app --reload

# Unit tests only (no database needed)
uv run pytest

# PostgreSQL integration tests (requires running container)
uv run pytest -m postgres

# All tests
uv run pytest -m ''

# Architecture lint
uv run lint-imports
```

## Database

PostgreSQL via Docker Compose. Connection: `postgresql+asyncpg://vss:vss@localhost:5432/vss`

Schema managed by Alembic (`infra/postgres/alembic/`). Migrations run automatically on container startup.

Before running integration tests (`-m postgres`), the PostgreSQL container must be running and the test database must exist. Ask the user to start it if needed:

```bash
# From repo root (/home/feidon/Documents/vss)
sudo docker compose up -d

# Create test database (one-time)
sudo docker exec <container> psql -U vss -c "CREATE DATABASE vss_test;"
```

## Persistence Strategy: SQLAlchemy Core + Manual Mapper

**Do NOT use SQLAlchemy ORM mapping (neither declarative nor imperative).** Use SQLAlchemy Core with manual mapping in repositories.

Rationale:
- Domain models must be pure Python dataclasses with zero SQLAlchemy imports
- Repositories handle translation between domain entities and DB rows via `_to_entity()` / `_to_table()` methods
- SQLAlchemy Core (`select()`, `insert()`, `update()`, `delete()` on `Table` objects) for all queries
- No change tracking, no identity map, no lazy loading — all persistence is explicit
- Repositories use explicit `create()` and `update()` methods — no generic `save()` or upsert
- Reference data repos (Block, Vehicle, Station) only expose `update()` — creation is handled by seed migrations
- Service path/timetable stored as JSONB (aggregate storage — loaded/persisted as whole units)

This mirrors the QueryDSL SQL + Flyway pattern: schema-first, codegen/table definitions separate from domain, explicit mapper at repository boundary.

### Read and Write paths

Currently all reads and writes go through domain repositories. If a read endpoint needs joins across multiple aggregates that don't map to a single domain entity, introduce a query service with direct SQL returning DTOs — bypassing the domain layer (CQRS-lite). Until then, keep the single path.

### Cross-aggregate data

In a monolith with single DB, prefer querying at use time (load both aggregates in the application service) over snapshots + domain events. Pass data into domain logic from the application layer. Don't pay microservice complexity costs in a monolith.

## Testing Patterns

- **Domain tests**: pure unit tests, no I/O
- **Application tests**: async integration with in-memory repos from `tests/fakes/`, `@pytest.mark.asyncio`
- **API tests**: PostgreSQL integration tests via `httpx.AsyncClient`, marked `@pytest.mark.postgres`
- **Infra tests**: repository contract verification against PostgreSQL, marked `@pytest.mark.postgres`
- Helper factories: `make_block()`, `make_service_with_window()`, seed data utilities

## Notes

- No high-concurrency support
- No "stop at block" support — vehicles only dwell at platforms and yard

# VSS Backend

## Tech Stack

- Python 3.14 + FastAPI
- PostgreSQL 17 (Docker)
- Package manager: uv

## Architecture

Hexagonal Architecture (Ports & Adapters) with DDD:

```
backend/
├── api/            # FastAPI routes, Pydantic schemas, DI container
├── application/    # App services, DTOs, orchestration
├── domain/         # Entities, value objects, repository interfaces, domain services
├── infra/          # PostgreSQL repos, in-memory test doubles, seed data
└── tests/          # Mirrors source structure: domain/, application/, api/, infra/
```

Dependency flow: `api → application → domain ← infra`

## Key Domain Services

- **ConflictDetectionService**: detects vehicle, block occupancy, interlocking, and battery conflicts
- **RouteFinder**: BFS pathfinding to insert intermediate blocks between platform stops

## API Endpoints

| Method | Path                            | Description              |
|--------|---------------------------------|--------------------------|
| GET    | `/graph`                        | Full track network graph |
| GET    | `/blocks`                       | List all blocks          |
| GET    | `/blocks/{id}`                  | Get block by ID          |
| PATCH  | `/blocks/{id}`                  | Update traversal time    |
| POST   | `/services`                     | Create service           |
| GET    | `/services`                     | List all services        |
| GET    | `/services/{id}`                | Get service by ID        |
| PATCH  | `/services/{id}/route`          | Update service route     |
| POST   | `/routes/validate`              | Validate stops queue     |
| DELETE | `/services/{id}`                | Delete service           |

Route update returns 409 with conflict details when scheduling conflicts are detected.

### Validation Scope Split

- **`POST /routes/validate` (during editing):** Route connectivity + single-service battery only. No cross-service conflict checks — the route isn't final during editing.
- **`PATCH /services/{id}/route` (save):** Full cross-service conflict detection (vehicle, block, interlocking, battery) against all existing services.

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
```

## Database

PostgreSQL via Docker Compose. Connection: `postgresql://vss:vss@localhost:5432/vss`

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
- `save()` uses upsert (insert on conflict update all columns) — no need to diff changes

This mirrors the QueryDSL SQL + Flyway pattern: schema-first, codegen/table definitions separate from domain, explicit mapper at repository boundary.

### Write vs Read paths (CQRS-lite)

- **Write side (commands)**: Use repositories, load aggregates separately, enforce domain rules. Multiple queries across aggregates is fine.
- **Read side (queries)**: Use direct SQL with joins for list/display endpoints. No aggregate boundaries needed. Return DTOs, not domain entities.

### Cross-aggregate data

In a monolith with single DB, prefer querying at use time (load both aggregates in the application service) over snapshots + domain events. Pass data into domain logic from the application layer. Don't pay microservice complexity costs in a monolith.

## Testing Patterns

- **Domain tests**: pure unit tests, no I/O
- **Application tests**: integration with in-memory repos, `@pytest.mark.asyncio`
- **API tests**: PostgreSQL integration tests via `httpx.AsyncClient`, marked `@pytest.mark.postgres`
- **Infra tests**: repository contract verification against PostgreSQL, marked `@pytest.mark.postgres`
- Helper factories: `make_block()`, `make_service_with_window()`, seed data utilities


## Notes

- no "高併發" support
- no "stop at block" support

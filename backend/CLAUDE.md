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
├── infra/          # In-memory repository implementations, seed data
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
| DELETE | `/services/{id}`                | Delete service           |

Route update returns 409 with conflict details when scheduling conflicts are detected.

## Running

```bash
uv sync
uv run uvicorn main:app --reload

# Tests
uv run pytest
```

## Database

PostgreSQL via Docker Compose. Connection: `postgresql://vss:vss@localhost:5432/vss`

## Testing Patterns

- **Domain tests**: pure unit tests, no I/O
- **Application tests**: integration with in-memory repos, `@pytest.mark.asyncio`
- **API tests**: `TestClient` with dependency overrides
- **Infra tests**: repository contract verification
- Helper factories: `make_block()`, `make_service_with_window()`, seed data utilities

# Vehicle Scheduling System (VSS)

## Project Overview

Interview assignment: a vehicle scheduling system (frontend + backend) for managing railway vehicle services on a fixed track network with stations, platforms, blocks, and interlocking constraints.

## Tech Stack

| Layer          | Technology                    |
|----------------|-------------------------------|
| Backend        | Python 3.14 + FastAPI         |
| Frontend       | Angular (latest stable) - TBD |
| Database       | PostgreSQL 17 (Docker)         |
| Containerization | Docker + Docker Compose      |
| Package Manager | uv                           |
| Node (frontend) | managed via mise (LTS)       |

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

## Domain Model

- **Block**: track segment with traversal time, interlocking group (1-3 or none)
- **Station**: has platforms (2 each); Yard (Y) is a special station
- **Platform**: P1A, P1B, P2A, P2B, P3A, P3B
- **Service**: scheduled vehicle run with path (nodes) and timetable (arrival/departure times)
- **Vehicle**: V1, V2, V3
- **Node** (value object): represents a point in the network (BLOCK, PLATFORM, or YARD)
- **NodeConnection** (value object): directed edge in the track graph
- **TimetableEntry** (value object): order + node_id + arrival/departure times

Key domain services:
- **ConflictDetectionService**: detects vehicle, block occupancy, and interlocking conflicts
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
# PostgreSQL
docker compose up -d

# Backend
cd backend
uv sync
uv run uvicorn main:app --reload

# Tests
cd backend
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

## Track Network

14 blocks (B1-B14), 4 stations (Y, S1, S2, S3), 6 platforms. Blocks are unidirectional. Three interlocking groups enforce mutual exclusion:
- Group 1: B1, B2
- Group 2: B3, B4, B13, B14
- Group 3: B7, B8, B9, B10

## Requirement Status

### Core (mandatory)
- [x] Service definition (path + timetable)
- [x] Schedule CRUD with path connectivity validation
- [ ] Schedule Editor page (frontend)
- [ ] Schedule Viewer page (frontend)
- [x] Block Configuration (backend API done, frontend TBD)
- [x] Unit tests

### Bonus
- [x] Bonus 1 — Conflict detection (block occupancy, interlocking, vehicle conflicts)
- [ ] Bonus 1 — Low battery / insufficient charge detection
- [ ] Bonus 2 — Interactive track map (d3.js)
- [ ] Bonus 3 — Auto-generate schedule
- [ ] Docker + Docker Compose setup

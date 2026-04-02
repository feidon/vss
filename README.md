# Vehicle Scheduling System (VSS)

A vehicle scheduling system for managing transit services on a fixed track network. Operators create services (scheduled vehicle runs), define routes by selecting stops (platforms or yard), and the system auto-fills intermediate blocks, computes timetables, and detects scheduling conflicts.

## Quick Start

```bash
docker compose up
```

Open **http://localhost:8000** once all services are ready.

### Prerequisites

- Docker & Docker Compose

### Services

| Service    | Internal Port | Exposed Port | Description                                        |
|------------|---------------|--------------|----------------------------------------------------|
| `postgres` | 5432          | 5432         | PostgreSQL 17 database                             |
| `backend`  | 8000          | 8000         | Python 3.14 + FastAPI, also serves the Angular SPA |

The Angular frontend is built inside the backend Docker image and served by FastAPI as static files. API routes (`/blocks`, `/services`, `/graph`, `/routes`) are handled first; all other paths fall back to `index.html` for SPA routing. The database schema and seed data (stations, platforms, blocks, vehicles, connections) are created automatically on startup.

### Local Development (without Docker)

**Backend:**

```bash
cd backend
uv sync
# PostgreSQL must be running (see docker compose up -d)
uv run uvicorn main:app --reload
```

**Frontend:**

```bash
cd frontend
npm install
ng serve    # http://localhost:4200, API calls go to http://localhost:8000
```

**Tests:**

```bash
cd backend
uv run pytest              # unit tests (no DB needed)
uv run pytest -m postgres  # integration tests (needs PostgreSQL)
uv run pytest -m ''        # all tests
uv run lint-imports        # verify architectural layer dependencies
```

---

## Architecture

### DDD + Clean Architecture

The backend follows **Domain-Driven Design** with **Clean Architecture** layering (Ports & Adapters):

```
api/  →  application/  →  domain/  ←  infra/
```

| Layer            | Role                          | Contents                                              |
|------------------|-------------------------------|-------------------------------------------------------|
| **`domain/`**    | Core business rules           | Entities, value objects, repository interfaces (ports), domain services |
| **`application/`** | Use-case orchestration     | Coordinates domain objects and repos; enforces workflow (build route → detect conflicts → persist) |
| **`api/`**       | Inbound adapter               | FastAPI routes, Pydantic schemas, dependency injection |
| **`infra/`**     | Outbound adapters             | PostgreSQL repositories (production), in-memory repositories (test doubles) |

Dependencies point inward — `infra` implements domain interfaces, `api` calls application services, but **nothing depends on `infra` or `api`** from inside the domain. This is enforced at CI time via [`import-linter`](https://github.com/seddonym/import-linter).

### Rich Domain Model

Entities encapsulate behavior, not just data:

| Entity      | Key Behavior                                                                 |
|-------------|------------------------------------------------------------------------------|
| **Block**   | Validates `traversal_time_seconds > 0`; converts itself to `Node` and `TimetableEntry` |
| **Vehicle** | Manages battery: `charge()`, `traverse_block()`, `can_depart()`, `is_battery_critical()` |
| **Service** | Enforces route invariants on `update_route()`: timetable ordering, time continuity, path connectivity |
| **Station** | Owns platforms; guards duplicate IDs; only yards produce `Node` representations |

Domain services handle cross-aggregate logic:

| Service                      | Responsibility                                                              |
|------------------------------|-----------------------------------------------------------------------------|
| **ConflictDetectionService** | Detects vehicle, block, interlocking, and battery conflicts (sweep-line + simulation) |
| **RouteFinder**              | BFS pathfinding to infer intermediate blocks between stops                  |

Both are pure functions — no repository access, no state.

### Repository Pattern

Each aggregate root defines an abstract repository interface (port) in `domain/`:

```python
# domain/block/repository.py
class BlockRepository(ABC):
    async def find_all(self) -> list[Block]: ...
    async def find_by_id(self, id: UUID) -> Block | None: ...
    async def save(self, block: Block) -> None: ...
```

`infra/` provides concrete adapters — one for PostgreSQL, one in-memory:

```python
# infra/postgres/block_repo.py        — talks to the database
class PostgresBlockRepository(BlockRepository): ...

# infra/memory/block_repo.py          — dict-backed, no I/O
class InMemoryBlockRepository(BlockRepository): ...
```

The domain declares **what** it needs; adapters decide **how**. Application services and domain logic depend only on the interface, never on a concrete implementation. FastAPI's `Depends()` wires PostgreSQL repositories at runtime. In-memory repositories are used exclusively as test doubles in application-level tests.

This is the Ports & Adapters pattern in action: the repository interface is the **port**, and each implementation is an **adapter**. See [Trade-off #4](#4-dual-repository-strategy-in-memory--postgresql) for the dual-implementation rationale and [Trade-off #5](#5-sqlalchemy-core--manual-mapper-vs-orm) for the persistence technology choice.

---

## Data Model

### Entity Relationship

```
Station (1) ──── (*) Platform
   │
   └── is_yard: bool (Y is the depot)

Vehicle ──── battery, charge/drain logic

Service ──── name, vehicle_id
   ├── path: [Node]              (ordered: platforms + blocks + yard)
   └── timetable: [TimetableEntry]  (arrival/departure per node)

Block ──── traversal_time_seconds, group (interlocking)

NodeConnection ──── from_id → to_id (directed graph edges)
```

### Core Entities

| Entity       | Key Fields                                   | Notes                                        |
|--------------|----------------------------------------------|----------------------------------------------|
| **Station**  | id, name, is_yard, platforms[]               | 4 stations: Y (yard), S1, S2, S3             |
| **Platform** | id, name                                     | 6 platforms: P1A, P1B, P2A, P2B, P3A, P3B    |
| **Block**    | id, name, group, traversal_time_seconds      | 14 blocks (B1-B14), group 0 = no interlocking |
| **Vehicle**  | id, name, battery                            | 3 vehicles: V1, V2, V3                       |
| **Service**  | id, name, vehicle_id, path[], timetable[]    | A scheduled vehicle run                      |

### Service Path & Timetable

A **service** represents a single vehicle run. The user selects stops (platforms or yard) and dwell times; the system uses BFS to find intermediate blocks and computes the full timetable:

```
User input:  stops = [P1A (dwell 60s), P2A (dwell 45s)]
                              ↓ RouteFinder (BFS)
Full path:   [P1A, B3, B5, P2A]
Timetable:   P1A  arr=T+0    dep=T+60    (60s dwell)
             B3   arr=T+60   dep=T+90    (30s traversal)
             B5   arr=T+90   dep=T+120   (30s traversal)
             P2A  arr=T+120  dep=T+165   (45s dwell)
```

Each timetable entry's departure equals the next entry's arrival (continuous time). Block durations come from the configurable `traversal_time_seconds`.

### Database Schema

PostgreSQL with SQLAlchemy Core tables (no ORM):

| Table              | PK        | Notable Columns                        |
|--------------------|-----------|----------------------------------------|
| `stations`         | UUID      | name, is_yard                          |
| `platforms`        | UUID      | name, station_id (FK)                  |
| `blocks`           | UUID      | name, group, traversal_time_seconds    |
| `vehicles`         | UUID      | name                                   |
| `services`         | int (auto)| name, vehicle_id (FK), path (JSONB), timetable (JSONB) |
| `node_connections` | (from, to)| Directed edges of the track graph      |

---

## API Design

Base URL: `http://localhost:8000`

### Endpoints

| Method | Path                         | Description                              |
|--------|------------------------------|------------------------------------------|
| GET    | `/graph`                     | Full track network: nodes, edges, stations, vehicles |
| GET    | `/blocks`                    | List all blocks with traversal times     |
| PATCH  | `/blocks/{id}`               | Update a block's traversal time          |
| POST   | `/services`                  | Create a new service (empty route)       |
| GET    | `/services`                  | List all services with full path & timetable |
| GET    | `/services/{id}`             | Get a single service                     |
| PATCH  | `/services/{id}/route`       | Update route (validates + detects conflicts) |
| POST   | `/routes/validate`           | Validate stops list without persisting   |
| DELETE | `/services/{id}`             | Delete a service                         |

### Service Lifecycle

1. **Create** — `POST /services` with name + vehicle_id. Returns a service with empty path/timetable.
2. **Define route** — `PATCH /services/{id}/route` with stops (`node_id` — platform or yard UUIDs), dwell times, and start time. The backend:
   - Validates all stops exist (platforms and yard)
   - Uses BFS to find blocks between consecutive stops
   - Computes arrival/departure times from block traversal times and dwell times
   - Runs full conflict detection against all other services
   - Returns **409** with detailed conflicts if any are found, otherwise persists and returns **200**
3. **Delete** — `DELETE /services/{id}`

### Conflict Detection (409 Response)

When updating a route, the system checks for these conflict types:

| Conflict Type          | Description                                                     |
|------------------------|-----------------------------------------------------------------|
| Vehicle time overlap   | Same vehicle assigned to services with overlapping time windows |
| Location discontinuity | Vehicle's last position doesn't match next service's start      |
| Block occupancy        | Two services occupy the same block at overlapping times         |
| Interlocking           | Blocks in the same interlocking group occupied simultaneously   |
| Low battery            | Vehicle battery drops below 30 outside the yard                 |
| Insufficient charge    | Vehicle departs yard with battery below 80                      |

Conflict response includes structured details (block IDs, overlap windows, reasons) so the frontend can display actionable information.

### Design Principles

- **Nouns as paths** (`/services`, `/blocks`) rather than verbs
- **HTTP methods** map to operations (GET=read, POST=create, PATCH=update, DELETE=remove)
- **Route update is a sub-resource** (`/services/{id}/route`) — distinct operation with different validation and side effects than updating service metadata
- **409 for conflicts** rather than 400 — the request is valid in isolation; the conflict arises from the current state of other services

---

## Design Trade-offs

### Domain & Behavior

#### 1. Two-Phase Validation: Light Check During Editing, Full Check on Save

**Choice:** Conflict detection is split into two scopes:
- **During editing** — route connectivity (can the path be built?) and single-service battery simulation only. No cross-service checks.
- **On save** (`PATCH /services/{id}/route`) — full cross-service conflict detection: vehicle overlap, block occupancy, interlocking, and battery conflicts against all existing services.

**Why:** Checking all services on every stop addition is wasteful and confusing — a half-built route will almost always conflict with something. By scoping validation to what's useful at each phase, the user gets relevant feedback without noise.

**Trade-off:** The user doesn't learn about cross-service conflicts until they try to save. Acceptable because the conflict response is detailed enough to guide fixes, and the route can be re-edited immediately.

#### 2. BFS Route Inference vs Manual Full-Path Specification

**Choice:** Users select only stops (platforms/yard); the system uses BFS to find intermediate blocks automatically.

**Why:** The track network has a fixed topology where there's typically one valid block chain between any two stops. Requiring users to manually specify every block would be tedious and error-prone. BFS guarantees a valid connected path and simplifies the API contract (just node IDs and dwell times).

**Trade-off:** BFS picks the shortest path, removing user choice if multiple routes exist. In this track map, most stop pairs have a single path, so no choice is lost.

### Persistence & Data

#### 3. JSONB Aggregate Storage vs Normalized Join Tables

**Choice:** Store `path` and `timetable` as JSONB arrays on the `services` row rather than in separate `service_path_nodes` and `service_timetable_entries` tables.

**Why:** A service is always loaded and persisted as a whole — path and timetable are never queried independently. JSONB keeps reads and writes as single-row operations, avoids N+1 query patterns, and simplifies the repository layer. The `save()` method uses upsert, so there's no need to diff or reconcile child rows.

**Trade-off:** Cross-service queries (e.g., "which services pass through block B3?") require scanning JSONB across all rows. Acceptable because conflict detection already loads all services into memory.

#### 5. SQLAlchemy Core + Manual Mapper vs ORM

**Choice:** Use SQLAlchemy Core (`select()`, `insert()`, `update()` on `Table` objects) with hand-written `_to_entity()` / `_to_table()` mapper methods in each repository. No declarative models, no imperative mapping, no `Session.add()`.

**Why:** The domain follows DDD with rich entities that must remain free of persistence concerns. SQLAlchemy ORM mapping (even imperative) leaks into the domain via session management, identity maps, and change tracking. With Core + manual mapper:
- Domain entities have zero SQLAlchemy imports — just `@dataclass` classes
- Persistence is fully explicit: `save()` uses upsert, reads use `select()`, no hidden queries
- No identity map, no lazy loading, no change tracking
- Mirrors the QueryDSL SQL + Flyway pattern: schema-first tables, explicit mapper at the repository boundary

**Trade-off:** More boilerplate per repository (`_to_entity()` / `_to_table()` methods). Acceptable because the mapping is straightforward, co-located with the SQL, and the only place where schema changes need updating.

### Infrastructure

#### 4. Dual Repository Strategy (In-Memory for Tests + PostgreSQL for Production)

**Choice:** Every repository interface has both an in-memory and a PostgreSQL implementation. Production always uses PostgreSQL; in-memory repos are used exclusively as test doubles in application-level tests.

**Why:** In-memory repos enable fast application-level testing without database setup — domain and application tests run in milliseconds. PostgreSQL repos are exercised by dedicated integration tests marked with `@pytest.mark.postgres`. The DI container unconditionally wires PostgreSQL; test fixtures inject in-memory repos directly.

**Trade-off:** Maintaining two implementations per repository adds code. Mitigated by narrow repository interfaces (5 methods or fewer) and integration tests verifying both implementations against the same contracts.

---

## Assumptions

### Domain Constraints

1. **Fixed track topology** — The 14 blocks, 4 stations, 6 platforms, and their connections are seeded on startup and not user-editable.
2. **Fixed vehicle fleet** — Three vehicles (V1, V2, V3) are pre-seeded. No UI or API to add/remove vehicles.
3. **Battery parameters are constants** — Initial battery 80, max 100, cost 1 per block, low threshold 30, charge rate 12 seconds/unit, required 80 on departure. Per the assignment spec.
4. **Vehicles cannot stop at blocks** — Vehicles only dwell at platforms and the yard. Blocks are pass-through segments with fixed traversal time.
5. **Block traversal is instantaneous entry** — A vehicle occupies a block for exactly `traversal_time_seconds` from arrival. No acceleration/deceleration modeling.
6. **Single valid path between most stops** — BFS always picks the shortest block chain. The current track map has at most one path between any stop pair, so no user choice is lost.
7. **Services are independent runs** — No concept of "chaining" services into a vehicle's daily schedule. Conflict detection handles overlaps between independent services.

### Scope Boundaries

8. **Single-user system** — No authentication, authorization, or concurrent editing support.
9. **No concurrent editing or service versioning** — Last write wins. No optimistic locking, no version field, no conflict resolution for simultaneous edits.
10. **No high-concurrency support** — No connection pooling tuning, no rate limiting, no caching layer.
11. **Small number of services** — Conflict detection loads all services into memory on every route save. Suitable for dozens or hundreds of services, not thousands.

### Technical Choices

12. **Time in Unix epoch seconds** — All timetable times use integer Unix timestamps. The frontend converts to/from local datetime for display. Avoids timezone complexity.

---

## Project Structure

```
vss/
├── docker-compose.yml
├── requirement.md
│
├── backend/
│   ├── Dockerfile
│   ├── main.py                  # FastAPI app, lifespan (table creation + seeding)
│   ├── pyproject.toml           # Python 3.14, uv
│   ├── api/                     # Routes, Pydantic schemas, dependency injection
│   ├── application/             # App services, DTOs, orchestration
│   ├── domain/                  # Entities, value objects, repo interfaces, domain services
│   ├── infra/                   # PostgreSQL repos (production), in-memory repos (test doubles)
│   └── tests/                   # Unit + integration tests
│
└── frontend/
    ├── angular.json
    └── src/app/
        ├── core/services/       # API client services
        ├── shared/models/       # TypeScript interfaces
        └── features/
            ├── schedule-editor/ # Create/edit/delete services and routes
            ├── schedule-viewer/ # Read-only timetable display
            ├── block-config/    # Block traversal time editing
            └── track-map/       # d3.js interactive visualization (bonus)
```

## Todo

- [x] in-memory repo only for tests
- [ ] create ci
- [ ] create domain error and error handler
- [ ] not consist starlette.status
- [ ] some domain login leak to `backend/application/service/service.py`
- [ ] route/path mismatch in service entity
- [ ] refactor `backend/application/service/service.py`, there are too many same query and hard to read

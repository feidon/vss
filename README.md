# Vehicle Scheduling System (VSS)

A vehicle scheduling system for managing transit services on a fixed track network. Operators create services (scheduled vehicle runs), define routes by selecting stops, and the system auto-fills intermediate blocks, computes timetables, and detects scheduling conflicts.

## Quick Start

```bash
docker compose up
```

Open **http://localhost** once all services are ready. That's it.

### Prerequisites

- Docker & Docker Compose
- **BuildKit / buildx** — `backend/Dockerfile` uses `# syntax=docker/dockerfile:1` and a `RUN --mount=type=cache` directive, both of which require the BuildKit builder. Docker Desktop and recent Docker Engine releases ship buildx by default. On Arch/CachyOS install it explicitly: `sudo pacman -S docker-buildx`. Verify with `docker buildx version`.

### What Happens on Startup

1. PostgreSQL initializes
2. Backend runs Alembic migrations (creates schema + seeds reference data)
3. Backend starts FastAPI on port 8000
4. Frontend (nginx) serves the Angular SPA on port 80 and proxies `/api/*` to the backend

| Service    | Port (internal) | Port (exposed) | Description                |
|------------|-----------------|----------------|----------------------------|
| `postgres` | 5432            | 5432           | PostgreSQL 17              |
| `backend`  | 8000            | --             | Python 3.14 + FastAPI      |
| `frontend` | 80              | 80             | Angular 21 SPA via nginx   |

### Local Development (without Docker)

**Backend:**

```bash
cd backend
uv sync
# Start PostgreSQL: docker compose up -d postgres
uv run uvicorn main:app --reload    # http://localhost:8000/api
```

**Frontend:**

```bash
cd frontend
npm install
ng serve    # http://localhost:4200, proxies API to localhost:8000
```

**Tests:**

```bash
# Backend
cd backend
uv run pytest              # unit tests (no DB needed)
uv run pytest -m postgres  # integration tests (needs PostgreSQL)
uv run pytest -m ''        # all tests
uv run lint-imports        # verify architecture layer constraints

# Frontend
cd frontend
ng test                    # Vitest unit tests
ng lint                    # ESLint
```

---

## Data Model

### Entity Relationship

```
Station (1) ---- (*) Platform
   |
   └── is_yard: bool (Y = depot)

Vehicle ---- battery, charge/drain logic

Service ---- name, vehicle_id
   ├── route: [Node]               (ordered: platforms + blocks + yard)
   └── timetable: [TimetableEntry] (arrival/departure per node)

Block ---- traversal_time_seconds, group (interlocking)

NodeConnection ---- from_id -> to_id (directed graph edges)
```

### Core Entities

| Entity       | Key Fields                                | Notes                                       |
|--------------|-------------------------------------------|---------------------------------------------|
| **Station**  | id, name, is_yard, platforms[]            | 4 stations: Y (yard), S1, S2, S3            |
| **Platform** | id, name                                  | 6 platforms: P1A, P1B, P2A, P2B, P3A, P3B   |
| **Block**    | id, name, group, traversal_time_seconds   | 14 blocks (B1-B14), group 0 = no interlocking |
| **Vehicle**  | id, name, battery                         | Seeded with V1, V2, V3; schedule generator adds more as needed |
| **Service**  | id, name, vehicle_id, route[], timetable[] | A scheduled vehicle run                    |

### How Route Building Works

Users select stops (platforms or yard) and dwell times. The system fills in the rest:

```
User input:  stops = [P1A (dwell 60s), P2A (dwell 45s)], start_time = T

    --> BFS finds intermediate blocks

Full route:  P1A -> B3 -> B5 -> P2A

Timetable:   P1A  arr=T       dep=T+60    (60s dwell)
             B3   arr=T+60    dep=T+90    (30s traversal)
             B5   arr=T+90    dep=T+120   (30s traversal)
             P2A  arr=T+120   dep=T+165   (45s dwell)
```

### Design Rationale

The domain follows **DDD with rich entities** -- entities encapsulate behavior, not just data. For example, `Vehicle` manages its own battery state (`charge()`, `traverse_block()`, `can_depart()`), and `Service` enforces route invariants on update.

**Why JSONB for route/timetable?** A service is always loaded and saved as a whole -- route and timetable are never queried independently. JSONB keeps it as single-row operations and avoids N+1 joins. Cross-service queries (conflict detection) already load all services into memory anyway.

### Database Schema

| Table              | PK          | Notable Columns                     |
|--------------------|-------------|-------------------------------------|
| `stations`         | UUID        | name, is_yard                       |
| `platforms`        | UUID        | name, station_id (FK)               |
| `blocks`           | UUID        | name, group, traversal_time_seconds |
| `vehicles`         | UUID        | name                                |
| `services`         | int (auto)  | name, vehicle_id (FK), route (JSONB), timetable (JSONB) |
| `node_connections` | (from, to)  | Directed graph edges                |
| `node_layouts`     | UUID        | x, y coordinates for visualization  |
| `junction_blocks`  | (from_block, to_block) | junction_id (FK to node_layouts) — maps block pairs to the visual junction between them |

Schema managed by Alembic. Reference data (stations, blocks, vehicles, connections) is seeded in the migration.

---

## API Design

All endpoints are under `/api`. In Docker: `http://localhost/api`. Local dev: `http://localhost:8000/api`.

| Method | Path                         | Description                              |
|--------|------------------------------|------------------------------------------|
| POST   | `/api/services`              | Create a new service (empty route)       |
| GET    | `/api/services`              | List services (summary view)             |
| GET    | `/api/services/{id}`         | Get service detail with route, timetable, graph |
| PATCH  | `/api/services/{id}/route`   | Update route (validates + detects conflicts) |
| DELETE | `/api/services/{id}`         | Delete a service                         |
| GET    | `/api/blocks`                | List all blocks with traversal times     |
| PATCH  | `/api/blocks/{id}`           | Update a block's traversal time          |
| GET    | `/api/vehicles`              | List all vehicles                        |
| POST   | `/api/schedules/generate`    | Replace all services with an auto-generated, conflict-free schedule (adds vehicles if needed) |

### Service Lifecycle

1. **Create** -- `POST /api/services` with name + vehicle_id. Returns a service with empty route.
2. **Define route** -- `PATCH /api/services/{id}/route` with stops (platform/yard UUIDs), dwell times, and start time. The backend validates connectivity, computes the timetable via BFS, runs conflict detection against all other services, and either persists (200) or returns conflicts (409).
3. **Delete** -- `DELETE /api/services/{id}`.

### Conflict Detection (409 Response)

When saving a route triggers conflicts, the response includes structured details:

| Conflict Type        | Description                                                  |
|----------------------|--------------------------------------------------------------|
| Vehicle overlap      | Same vehicle in services with overlapping time windows       |
| Block occupancy      | Two services occupy the same block at overlapping times      |
| Interlocking         | Blocks in same interlocking group occupied simultaneously    |
| Low battery          | Battery drops below 30 outside the yard                      |
| Insufficient charge  | Vehicle departs yard with battery below 80                   |

### Design Principles

- **Nouns as paths** (`/services`, `/blocks`), HTTP methods for operations
- **Route update as sub-resource** (`/services/{id}/route`) -- distinct validation logic from metadata updates
- **409 for conflicts** -- the request is valid in isolation; conflict arises from current state

---

## Architecture

### Hexagonal Architecture (Ports & Adapters)

```
  api/ --> application/ --> domain/ <-- infra/
  (inbound)  (use cases)     (core)    (outbound)
```

Dependencies point inward. Nothing in `domain/` imports from the outside. Enforced by [`import-linter`](https://github.com/seddonym/import-linter) at CI time.

| Layer            | Role                     | Contents                                                 |
|------------------|--------------------------|----------------------------------------------------------|
| **`domain/`**    | Core business rules      | Entities, value objects, repository interfaces, domain services |
| **`application/`** | Use-case orchestration | Coordinates domain + repos; workflow (build -> detect -> persist) |
| **`api/`**       | Inbound adapter          | FastAPI routes, Pydantic schemas, DI                     |
| **`infra/`**     | Outbound adapter         | PostgreSQL repositories, Alembic migrations, seed data   |

### Repository Pattern

Each aggregate defines an abstract interface in `domain/` (the **port**). Two implementations exist:

- **PostgreSQL** (`infra/postgres/`) -- production adapter
- **In-memory** (`tests/fakes/`) -- fast test double, no DB needed

FastAPI `Depends()` wires PostgreSQL at runtime. Tests inject in-memory repos directly.

---

## Design Trade-offs

### 1. SQLAlchemy Core + Manual Mapper vs ORM

**Chose:** SQLAlchemy Core with hand-written `_to_entity()` / `_to_table()` mapper methods. No ORM, no `Session.add()`.

**Why:** Domain entities must be pure Python dataclasses with zero SQLAlchemy imports. ORM mapping (even imperative) leaks persistence concerns via session management, identity maps, and change tracking. With Core + manual mapper, persistence is fully explicit and the domain stays clean.

**Trade-off:** More boilerplate per repository. Acceptable because the mapping is straightforward, co-located with the SQL, and the only place where schema changes need updating.

### 2. BFS Route Inference vs Manual Path Specification

**Chose:** Users select only stops (platforms/yard); the system infers intermediate blocks via BFS.

**Why:** The track topology has typically one valid block chain between stops. Requiring manual block-by-block input would be tedious and error-prone.

**Trade-off:** BFS picks shortest path, removing user choice. In this track map, most pairs have exactly one path, so no choice is lost.

### 3. JSONB Aggregate Storage vs Normalized Join Tables

**Chose:** Store service `route` and `timetable` as JSONB arrays on the service row.

**Why:** A service is always loaded/saved as a whole. JSONB avoids N+1 queries and simplifies the repository. Conflict detection already loads all services anyway.

**Trade-off:** Cross-service queries on individual nodes require JSONB scanning. Acceptable at this scale.

### 4. In-Memory Fakes vs Mocks for Application Tests

**Chose:** Hand-written in-memory fakes for every repository interface, living in `tests/fakes/` and used only by application-layer tests. Production DI (`api/dependencies.py`) unconditionally wires PostgreSQL — fakes never leak into production code.

**Why:** Fakes hold real state and implement the full interface, so tests exercise actual behavior (ID assignment, filtering, delete semantics) in sub-milliseconds with zero DB setup. Method-level mocks would couple tests to call signatures without catching state bugs. Postgres repos get their own contract tests at `tests/infra/` (`@pytest.mark.postgres`) to catch drift between fake and real.

**Trade-off:** Each interface needs a fake kept in sync with the Postgres implementation. Narrow interfaces (most ≤ 4 methods; `ServiceRepository` is the widest at 7) keep the cost small.

---

## Assumptions

### Domain

- **Fixed track topology** -- 14 blocks, 4 stations, 6 platforms are seeded and immutable; between any two consecutive stops there is at most one valid block chain, so BFS (over blocks only) returns a unique path. Only a block's `traversal_time_seconds` is editable; the graph itself is not.
- **Battery parameters are constants** -- initial 80, max 100, cost 1/block, low threshold 30, charge rate 12s/unit, departure requires 80.
- **Vehicles only dwell at platforms/yard** -- blocks are pass-through with fixed traversal time; there is no "stop at block" support.
- **Services are independent** -- no chaining into a daily schedule; each trip is a standalone `Service` record.
- **Traversal time changes don't retroactively update timetables** -- `PATCH /api/blocks/{id}` only updates the block row; re-save any affected route to recompute its timetable.
- **Vehicle fleet auto-grows** -- seeded with V1, V2, V3 and has no direct CRUD API. `POST /api/schedules/generate` sizes the fleet as `ceil(max_turnaround / (interval + dwell)) + 1` and calls `VehicleRepository.add_by_number()` to create any deficit. The `+1` (`FLEET_BUFFER` in `backend/application/schedule/network_layout.py`) absorbs rounding and timing slack so the scheduler never leaves a departure slot empty due to a fractionally-unavailable vehicle.

### Scope

- **Single-user system** -- no auth, no concurrent editing.
- **Small dataset** -- conflict detection loads all services in memory. Suitable for dozens/hundreds, not thousands.
- **Single-node monolith** -- no message queues, caching, distributed locking, or observability stack.
- **Time in Unix epoch seconds** -- avoids timezone complexity; frontend converts for display.

---

## Requirements Checklist

### Core Requirements

| #   | Requirement                  | Status | Notes                                                        |
|-----|------------------------------|--------|--------------------------------------------------------------|
| 1   | Service Definition           | Done   | Service with ID, vehicle, path, timetable                    |
| 2   | Schedule Management (CRUD)   | Done   | Create, list, detail, update route, delete                   |
| 2a  | Path connectivity validation | Done   | BFS validates consecutive blocks via adjacency               |
| 2b  | Vehicle conflict handling    | Done   | Detects overlapping time windows + location discontinuity    |
| 3a  | Schedule Editor page         | Done   | Route editor with stop selection, dwell times, start time    |
| 3b  | Schedule Viewer page         | Done   | Service list with summary (vehicle, origin, destination)     |
| 3c  | Block Configuration page     | Done   | Inline traversal time editing, grouped by interlocking       |
| 4   | Backend unit tests           | Done   | Domain, application, API, and infra test layers              |

### Bonus Requirements

| #     | Requirement                     | Status      | Notes                                                    |
|-------|---------------------------------|-------------|----------------------------------------------------------|
| B1    | Conflict Detection              | Done        | All 3 types implemented + interlocking (beyond spec)     |
| B1.1  | Block occupancy conflict        | Done        | Sweep-line detection, returns overlap windows             |
| B1.2  | Low battery                     | Done        | Battery simulation per service                           |
| B1.3  | Insufficient charge on departure| Done        | Checks battery >= 80 on yard departure                   |
| B2    | Interactive Track Map           | Done        | d3.js visualization of the full track network            |
| B2.1  | Interactive path editing        | Done        | Click platforms/yard/blocks on map to build route         |
| B2.2  | Schedule simulation / playback  | Not done    | --                                                       |
| B3    | Auto-generate schedule          | Done        | Generates conflict-free schedule for given interval/range |

### Technical Requirements

| Requirement      | Status | Notes                                      |
|------------------|--------|--------------------------------------------|
| Angular frontend | Done   | Angular 21, standalone components, signals |
| Python + FastAPI | Done   | Python 3.14, FastAPI, async                |
| PostgreSQL       | Done   | PostgreSQL 17, Alembic migrations          |
| Docker Compose   | Done   | Single `docker compose up` to run          |

---

## Project Structure

```
vss/
├── docker-compose.yml
├── requirement.md
│
├── backend/
│   ├── Dockerfile
│   ├── main.py                  # FastAPI app entry point
│   ├── pyproject.toml
│   ├── api/                     # Routes, schemas, DI
│   ├── application/             # App services, DTOs
│   ├── domain/                  # Entities, domain services, repo interfaces
│   ├── infra/
│   │   ├── seed.py              # Reference data seed (invoked by Alembic migration)
│   │   └── postgres/            # PostgreSQL repos, tables, Alembic migrations
│   └── tests/
│       ├── domain/              # Pure unit tests
│       ├── application/         # Integration with in-memory repos
│       ├── api/                 # PostgreSQL integration tests
│       ├── infra/               # Repository contract tests
│       └── fakes/               # In-memory repo implementations
│
└── frontend/
    ├── Dockerfile
    ├── nginx.conf               # Proxies /api/* to backend, SPA fallback
    └── src/app/
        ├── core/services/       # API client services
        ├── shared/models/       # TypeScript interfaces
        └── features/
            ├── schedule/        # Service list, editor, track map, auto-schedule
            └── config/          # Block config, vehicle list, track map overview
```

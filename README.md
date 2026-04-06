# Vehicle Scheduling System (VSS)

A vehicle scheduling system for managing transit services on a fixed track network. Operators create services (scheduled vehicle runs), define routes by selecting stops, and the system auto-fills intermediate blocks, computes timetables, and detects scheduling conflicts.

## Quick Start

```bash
docker compose up
```

Open **http://localhost** once all services are ready. That's it.

### Prerequisites

- Docker & Docker Compose

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
   ├── path: [Node]                (ordered: platforms + blocks + yard)
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
| **Vehicle**  | id, name, battery                         | 3 vehicles: V1, V2, V3                      |
| **Service**  | id, name, vehicle_id, path[], timetable[] | A scheduled vehicle run                     |

### How Route Building Works

Users select stops (platforms or yard) and dwell times. The system fills in the rest:

```
User input:  stops = [P1A (dwell 60s), P2A (dwell 45s)], start_time = T

    --> BFS finds intermediate blocks

Full path:   P1A -> B3 -> B5 -> P2A

Timetable:   P1A  arr=T       dep=T+60    (60s dwell)
             B3   arr=T+60    dep=T+90    (30s traversal)
             B5   arr=T+90    dep=T+120   (30s traversal)
             P2A  arr=T+120   dep=T+165   (45s dwell)
```

### Design Rationale

The domain follows **DDD with rich entities** -- entities encapsulate behavior, not just data. For example, `Vehicle` manages its own battery state (`charge()`, `traverse_block()`, `can_depart()`), and `Service` enforces route invariants on update.

**Why JSONB for path/timetable?** A service is always loaded and saved as a whole -- path and timetable are never queried independently. JSONB keeps it as single-row operations and avoids N+1 joins. Cross-service queries (conflict detection) already load all services into memory anyway.

### Database Schema

| Table              | PK          | Notable Columns                     |
|--------------------|-------------|-------------------------------------|
| `stations`         | UUID        | name, is_yard                       |
| `platforms`        | UUID        | name, station_id (FK)               |
| `blocks`           | UUID        | name, group, traversal_time_seconds |
| `vehicles`         | UUID        | name                                |
| `services`         | int (auto)  | name, vehicle_id (FK), path (JSONB), timetable (JSONB) |
| `node_connections` | (from, to)  | Directed graph edges                |
| `node_layouts`     | UUID        | x, y coordinates for visualization  |

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
| POST   | `/api/routes/validate`       | Validate route without saving            |
| GET    | `/api/blocks`                | List all blocks with traversal times     |
| PATCH  | `/api/blocks/{id}`           | Update a block's traversal time          |
| GET    | `/api/vehicles`              | List all vehicles                        |
| POST   | `/api/schedules/generate`    | Auto-generate a conflict-free schedule   |

### Service Lifecycle

1. **Create** -- `POST /api/services` with name + vehicle_id. Returns a service with empty route.
2. **Define route** -- `PATCH /api/services/{id}/route` with stops (platform/yard UUIDs), dwell times, and start time. The backend validates connectivity, computes the timetable via BFS, runs conflict detection against all other services, and either persists (200) or returns conflicts (409).
3. **Delete** -- `DELETE /api/services/{id}`.

### Two-Phase Validation

| Phase              | Endpoint                    | Checks                                        |
|--------------------|-----------------------------|------------------------------------------------|
| During editing     | `POST /api/routes/validate` | Route connectivity + single-service battery    |
| On save            | `PATCH /api/services/{id}/route` | Full cross-service conflicts (vehicle, block, interlocking, battery) |

Why split? A half-built route during editing will almost always conflict with something. Scoping validation to what's useful at each phase gives relevant feedback without noise.

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

**Chose:** Store service `path` and `timetable` as JSONB arrays on the service row.

**Why:** A service is always loaded/saved as a whole. JSONB avoids N+1 queries and simplifies the repository. Conflict detection already loads all services anyway.

**Trade-off:** Cross-service queries on individual nodes require JSONB scanning. Acceptable at this scale.

### 4. Dual Repository Strategy

**Chose:** Every repository interface has both in-memory and PostgreSQL implementations.

**Why:** In-memory repos enable sub-millisecond application tests without DB setup. PostgreSQL repos are verified by dedicated integration tests.

**Trade-off:** Two implementations to maintain. Mitigated by narrow interfaces (5 methods or fewer).

---

## Assumptions

### Domain

- **Fixed track topology** -- 14 blocks, 4 stations, 6 platforms are seeded and immutable.
- **Fixed vehicle fleet** -- V1, V2, V3 only. No API to add/remove.
- **Battery parameters are constants** -- Initial 80, max 100, cost 1/block, low threshold 30, charge rate 12s/unit, departure requires 80.
- **Vehicles only dwell at platforms/yard** -- blocks are pass-through with fixed traversal time.
- **Single valid path between most stops** -- BFS picks shortest; the track map has at most one path per pair.
- **Services are independent** -- no chaining into a daily schedule.
- **Traversal time changes don't retroactively update timetables** -- re-save a route to pick up new times.
- **Fleet sizing includes a 1-vehicle tolerance buffer** -- `num_vehicles = ceil(max_turnaround / interval) + 1`. The `+1` absorbs rounding and timing slack so the scheduler never leaves a departure slot empty due to a fractionally-unavailable vehicle. Defined as `FLEET_BUFFER` in `backend/application/schedule/network_layout.py`.

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
│   ├── infra/postgres/          # PostgreSQL repos, Alembic migrations, seed data
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

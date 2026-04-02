# Graph Layout & Route Validation Design

## Problem

The `/graph` endpoint returns pure topology (nodes + connections) but no spatial positioning. The frontend needs a render-ready track map where users can click platforms/yards to build service routes. Additionally, route building needs per-step validation without persisting incomplete routes.

## Design Decisions

### Node Layout: Separate Table

Coordinates are a rendering concern, not a domain concept. A `node_layouts` table stores hand-authored x/y positions.

```
node_layouts
├── node_id: UUID (PK)
├── x: float
├── y: float
```

- No domain entity — read-side only
- `NodeLayoutRepository` in `infra/` with a read-only interface
- `/graph` response merges coordinates into each node at the API layer
- Seeded with hand-authored positions for the fixed 21-node network

**Migration strategy:**
- Add table definition to `infra/postgres/tables.py`
- Create Alembic migration for the new table
- Seed coordinates via `infra/seed.py` (same pattern as existing seed data)
- Add in-memory implementation for local dev/testing

### Stops Field Naming: `node_id` Replaces `platform_id`

Since yards are now valid stops alongside platforms, the field name changes from `platform_id` to `node_id` across both endpoints:

- `POST /routes/validate` — uses `node_id` (new endpoint)
- `PATCH /services/{id}/route` — migrates from `platform_id` to `node_id`
- `RouteStop` DTO — migrates from `platform_id` to `node_id`
- `RouteStopInput` schema — migrates from `platform_id` to `node_id`
- Dwell time field: align to `dwell_time` (existing name, already in seconds)

**Validation changes:**
- `_validate_platforms_exist()` → `_validate_stops_exist()`: accepts both platform IDs and yard station IDs
- `_build_node_path()`: yard IDs included in node type mapping alongside platforms and blocks

**RouteFinder changes:**
- `find_block_chain()`: already works for yard-to-platform paths (yard connects to B1/B2 in seed data, BFS traverses blocks between any two non-block nodes)
- `build_full_path()`: yard IDs must be recognized as valid endpoints (not blocks). The `block_ids` set used for BFS filtering must exclude yard IDs just as it excludes platform IDs

### Route Validation Endpoint

```
POST /routes/validate

Request:
{
  "vehicle_id": "uuid",
  "stops": [
    {"node_id": "uuid", "dwell_time": 30}
  ],
  "start_time": int
}

Response (200):
{
  "path": ["uuid", ...],
  "battery_conflicts": [...]
}

Response (422):
{
  "detail": "No route from P3A to P1A"
}
```

**File location:** `api/route/routes.py` with `api/route/schemas.py` for request/response schemas.

**Path response format:** Bare UUIDs. The frontend already has the full graph from `GET /graph` and can cross-reference node details (type, name, etc.) locally. Sending rich node objects would duplicate data.

Frontend workflow:
1. User clicks platforms/yards on the map to build an ordered stops list
2. Each stop has a configurable dwell time (for passenger boarding or yard charging)
3. Same platform can appear multiple times (multi-lap services)
4. Frontend sends full stops list to `POST /routes/validate` after each addition
5. Backend expands full path via RouteFinder, computes timetable, checks single-service battery
6. Frontend shows expanded route on map + any battery warnings
7. When satisfied, user calls `PATCH /services/{id}/route` to persist

### Validation Scope Split

- **Validate (during editing):** Route connectivity (RouteFinder) + single-service battery simulation only. Cross-service conflicts are noise during editing since the route isn't final.
- **Save (`PATCH /services/{id}/route`):** Full cross-service conflict detection — vehicle, block, interlocking, and battery conflicts against all existing services. Unchanged behavior.

**Single-service battery mechanics:** Call `build_battery_steps(vehicle_id, [candidate_service_only])` — pass a list containing only the temporary service, not all services. This gives an isolated battery simulation for just the route being built. The function signature stays the same; the caller controls the scope by what it passes.

### Conflict Detector Reorganization

The current single-file `conflict.py` is split into a package for reusability:

```
domain/domain_service/conflict/
├── __init__.py          # re-export public API
├── model.py             # Value objects (ServiceConflicts, VehicleConflict, BlockConflict, etc.)
├── preparation.py       # Data building functions (public, no longer _prefixed)
├── detection.py         # Detection logic (sweep-line, overlap detection)
└── service.py           # Entry point: detect_conflicts()
```

Data preparation functions become public so the validation endpoint can call them independently for single-service checks.

**Bug fix during reorganization:** The existing `InsufficientChargeConflict` serialization in `api/service/routes.py` references `service_a_id` and `service_b_id`, but the domain model only has `service_id`. Fix this during the reorganization.

### Shared Route Building in ServiceAppService

Extract shared logic used by both validate and update. Both methods live on `ServiceAppService` — pragmatic choice since they share `_build_route` internals and the validate endpoint needs the same repositories (connections, blocks, stations, vehicles) minus `ServiceRepository`. The alternative (separate `RouteValidationAppService`) would require duplicating repository injection or extracting a shared helper. Not worth the indirection for a single shared method.

```
ServiceAppService:
    _build_route(stops, start_time, connections, blocks, stations)
        → validates stop IDs exist (platforms + yards)
        → expands path via RouteFinder
        → computes timetable from traversal/dwell times
        → returns (path, timetable)

    validate_route(vehicle_id, stops, start_time):
        path, timetable = _build_route(...)
        build temporary Service (no id, no persist)
        battery_conflicts = build_battery_steps(vehicle_id, [temp_service])
                          + detect_battery_conflicts(vehicle, steps)
        return (path, battery_conflicts)

    update_service_route(service_id, stops, start_time):
        path, timetable = _build_route(...)
        build temporary Service
        full cross-service conflict detection
        if conflicts → raise ConflictError (409)
        persist service
```

### No New Domain Concepts

- No "draft" status for services
- No route builder session or server-side state
- The stops list lives entirely in the frontend until save
- Yards are clickable stops just like platforms (with dwell time for charging)

## Existing Node Types Preserved

The discriminated union (`type: "block" | "platform" | "yard"`) stays. No merging of node types — the frontend uses `type` to decide styling (platform gets station marker, block is track segment, yard gets depot icon). The backend relies on the distinction for pathfinding and conflict detection.

**Note:** `GraphData.yard` property assumes a single yard. The current network has one yard, and this design does not change that assumption. If multiple yards are needed in the future, `yard` property and battery simulation logic would need updating.

## API Endpoints (Updated)

| Method | Path                            | Description                              |
|--------|---------------------------------|------------------------------------------|
| GET    | `/graph`                        | Full track network graph (now with x, y) |
| POST   | `/routes/validate`              | Validate stops list (no persist)         |
| GET    | `/blocks`                       | List all blocks                          |
| GET    | `/blocks/{id}`                  | Get block by ID                          |
| PATCH  | `/blocks/{id}`                  | Update traversal time                    |
| POST   | `/services`                     | Create service                           |
| GET    | `/services`                     | List all services                        |
| GET    | `/services/{id}`                | Get service by ID                        |
| PATCH  | `/services/{id}/route`          | Update service route (full validation)   |
| DELETE | `/services/{id}`                | Delete service                           |

## Context

The `GET /api/services` endpoint currently returns `{id, name, vehicle_id, vehicle_name}` per service. The frontend viewer needs start time, origin, and destination to render the list without N+1 detail fetches. All data already exists in the `route` (JSONB list of nodes) and `timetable` (JSONB list of entries) columns — no migration needed.

Current flow: `list_services()` loads all `Service` entities (including route/timetable), but the API schema discards everything except id/name/vehicle_id.

## Goals / Non-Goals

**Goals:**
- Add `start_time`, `origin_name`, `destination_name` to the list response
- Derive all values from existing persisted data at the API layer
- Handle newly created services with no route (fields are null)

**Non-Goals:**
- Optimizing the list query (e.g., extracting summary from JSONB in SQL) — current data size doesn't warrant it
- Adding pagination to the list endpoint
- Changing the domain model or adding new domain methods

## Decisions

### 1. Derive fields in the API schema's `from_domain()` method

The `ServiceResponse.from_domain()` class method already receives the full `Service` domain object. We'll extract summary fields there:

- `start_time` = `service.timetable[0].arrival` if timetable is non-empty, else `None`
- `origin_name` = `service.route[0].name` if route is non-empty, else `None`
- `destination_name` = last non-block node name in route (the final stop), else `None`

**Why at the schema layer**: This is a presentation concern — the domain model already has the data; we're just choosing which fields to expose. No new application service method needed.

**Alternative considered**: Adding a `ServiceSummaryDTO` at the application layer. Rejected — adds indirection for a simple field derivation that only the API needs.

### 2. `destination_name` uses the last stop node, not last route node

The last node in `route` could be a block (if the expanded path ends on a traversal segment). The destination should be the last platform or yard node, which is the meaningful "end" for the user.

**Why**: Route is the expanded full path including blocks. The last *stop* node (platform/yard) is the actual destination.

### 3. All new fields are optional (nullable)

Newly created services have empty route and timetable. Returning `null` for summary fields is cleaner than omitting them or using sentinel values.

## Risks / Trade-offs

- **[Performance]** `find_all()` loads full route/timetable JSONB for every service just to extract 3 summary fields → Acceptable for current scale (dozens of services). If list grows large, introduce a SQL projection or materialized summary column later.
- **[Contract]** Adding fields is non-breaking for existing clients → No risk.

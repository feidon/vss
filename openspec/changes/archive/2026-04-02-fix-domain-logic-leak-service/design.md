## Context

`ServiceAppService` in `backend/application/service/service.py` contains three private methods that perform domain logic:

- **`_validate_stops_exist`** — checks stop IDs against platforms and yards
- **`_build_node_path`** — resolves stop IDs into a full `list[Node]` with `NodeType` manually assigned via a dict
- **`_compute_timetable`** — computes `TimetableEntry` list with arrival/departure times based on block traversal times and dwell times

The domain models already have `to_node()` and `to_timetable_entry()` on `Block`, `Platform`, and `Station`/`Yard`, but the app service ignores them and duplicates the logic. This violates the hexagonal architecture where the application layer should only orchestrate.

## Goals / Non-Goals

**Goals:**

- Move route-building logic (path construction + timetable computation) into a `RouteBuilder` domain service
- Reuse existing `to_node()` / `to_timetable_entry()` methods on domain models
- Keep `ServiceAppService._build_route` as a thin orchestrator: load data, call `RouteBuilder`, return result

**Non-Goals:**

- Changing the API contract or response shapes
- Refactoring `RouteFinder` (it already lives in the domain layer)
- Modifying conflict detection logic
- Adding new features or capabilities

## Decisions

### 1. New `RouteBuilder` domain service at `domain/domain_service/route_builder.py`

**Rationale:** The logic is pure domain computation (no I/O). It fits alongside `RouteFinder` and the conflict detection services in `domain/domain_service/`. A domain service is the right home because the logic spans multiple aggregates (blocks, platforms, stations) and doesn't belong to any single entity.

**Alternative considered:** Adding methods to `Service` entity — rejected because `Service` shouldn't know how to resolve stops into paths (that requires block/station knowledge it doesn't own).

### 2. `RouteBuilder` accepts domain objects, not raw IDs

The method signature will accept `list[Block]`, `list[Station]`, and connections — not raw UUID sets. This lets it call `to_node()` and `to_timetable_entry()` directly on the models, eliminating the manual `NodeType` dict and timetable math in the app service.

**Alternative considered:** Passing pre-built lookup dicts — rejected because it pushes data-shaping responsibility to the caller, which is what we're trying to fix.

### 3. Stop validation moves into `RouteBuilder`

`_validate_stops_exist` is a domain invariant ("all stops must reference known platforms or yards"). It naturally belongs as a precondition of route building.

## Risks / Trade-offs

- **[Low] Test coverage gap** → Existing application-level tests cover the end-to-end flow. New domain-level unit tests for `RouteBuilder` will cover the extracted logic directly. Existing tests should pass without changes since behaviour is preserved.
- **[Low] Slightly more data loading** → `RouteBuilder` receives full domain objects instead of just IDs. The app service already loads these objects, so no additional DB queries are needed.

## Why

The Service entity stores `path: list[Node]` (the complete traversal sequence including intermediate blocks), but the application and API layers use "route" terminology (`update_service_route()`, `validate_route()`, `PATCH /services/{id}/route`, `POST /routes/validate`). Meanwhile, user input is called "stops" (`list[RouteStop]`). This three-way naming inconsistency (`stops` -> `route` -> `path`) makes the codebase harder to reason about — methods named `*route*` actually produce and modify `service.path`, and the RouteFinder domain service bridges stops-to-path with no actual Route concept in the domain.

## What Changes

- **Rename `Service.path` to `Service.route`** across domain, application, infra, and API layers — aligning the entity field with the operation name used everywhere else. **BREAKING** (API response field `path` becomes `route`).
- **Rename `RouteFinder.build_full_path()` to `RouteFinder.build_full_route()`** and rename its internal `path` variables accordingly.
- **Rename `RouteValidationResult.path` to `RouteValidationResult.route`** in the application DTO.
- **Rename API response fields**: `ValidateRouteResponse.path` -> `ValidateRouteResponse.route`, `ServiceDetailResponse.path` -> `ServiceDetailResponse.route`.
- **Update all tests** to use the new field name.

## Non-goals

- Introducing a new `Route` domain entity or value object — the list-of-nodes representation is sufficient.
- Changing the "stops" terminology — `RouteStop` and `stops` remain as-is since they clearly describe user input.
- Changing API endpoint paths (`/routes/validate`, `/services/{id}/route`) — these are already correct.

## Capabilities

### New Capabilities

- `route-field-rename`: Rename `path` to `route` across Service entity, DTOs, API schemas, repositories, and tests.

### Modified Capabilities

_(none — no existing spec-level behavior changes, only naming)_

## Impact

- **Domain**: `Service.path` field, `Service.compute_timetable()` internals, `RouteFinder` methods
- **Application**: `ServiceAppService`, `RouteValidationResult` DTO
- **API**: `ServiceDetailResponse`, `ValidateRouteResponse` schemas
- **Infra**: PostgreSQL repository mapping (`_to_entity()` / `_to_table()`) and DB column name
- **Tests**: All test files referencing `service.path` or `result.path`
- **Frontend**: Any consumer of `path` in API responses must update to `route` (breaking change)

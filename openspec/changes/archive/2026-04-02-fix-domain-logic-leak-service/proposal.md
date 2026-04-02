## Why

`ServiceAppService._build_node_path` and `_compute_timetable` manually construct `Node` objects and compute arrival/departure times — logic that already exists on domain models (`Block.to_node()`, `Platform.to_node()`, `Station.to_node()`, `Block.to_timetable_entry()`, `Platform.to_timetable_entry()`, `Station.to_timetable_entry()`). `_validate_stops_exist` performs domain validation (stop existence) that doesn't belong in the application layer. This duplication violates hexagonal architecture: the application service should orchestrate, not contain business rules.

## What Changes

- Extract `_build_node_path`, `_compute_timetable`, and `_validate_stops_exist` from `ServiceAppService` into a new `RouteBuilder` domain service
- `RouteBuilder` reuses existing `to_node()` and `to_timetable_entry()` methods on domain models instead of duplicating the logic
- `ServiceAppService._build_route` delegates to `RouteBuilder` instead of doing the work itself

## Capabilities

### New Capabilities

- `route-building`: Domain service that builds a full node path with timetable from a list of stops, using existing domain model methods and `RouteFinder`

### Modified Capabilities

(none — no existing spec-level requirements change)

## Impact

- **Code**: `backend/application/service/service.py` (slim down), new `backend/domain/domain_service/route_builder.py`
- **Tests**: New domain-level unit tests for `RouteBuilder`; existing application/API tests should continue to pass unchanged
- **APIs**: No API changes — behaviour is identical

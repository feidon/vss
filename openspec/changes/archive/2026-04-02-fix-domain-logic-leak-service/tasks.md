## 1. Create RouteBuilder domain service

- [x] 1.1 Create `backend/domain/domain_service/route_builder.py` with a `RouteBuilder` class
- [x] 1.2 Implement `validate_stops_exist` — accept stops, stations (with platforms), raise `DomainError` for unknown IDs
- [x] 1.3 Implement `build_node_path` — accept stops, connections, blocks, stations; use `RouteFinder.build_full_path` then resolve each ID to a `Node` via `to_node()` on the domain models
- [x] 1.4 Implement `compute_timetable` — accept full path, blocks, stations, dwell times, start_time; delegate to `to_timetable_entry()` on domain models
- [x] 1.5 Implement a top-level `build_route` method that chains validation, path building, and timetable computation

## 2. Update ServiceAppService to delegate

- [x] 2.1 Replace `_validate_stops_exist`, `_build_node_path`, `_compute_timetable` in `ServiceAppService` with a call to `RouteBuilder`
- [x] 2.2 Simplify `_build_route` to: load data from repos, call `RouteBuilder.build_route`, return result
- [x] 2.3 Remove unused imports from `service.py` (none to remove — all still used)

## 3. Tests

- [x] 3.1 Add domain-level unit tests for `RouteBuilder` in `backend/tests/domain/test_route_builder.py`
- [x] 3.2 Run existing application and API tests to verify no regressions

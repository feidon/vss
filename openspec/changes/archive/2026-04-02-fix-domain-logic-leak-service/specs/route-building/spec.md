## ADDED Requirements

### Requirement: RouteBuilder builds full node path from stops

`RouteBuilder` SHALL accept a list of stop node IDs, connections, blocks, and stations, and return a `list[Node]` representing the complete path (stops + intermediate blocks). It SHALL use `RouteFinder.build_full_path` for pathfinding and resolve each ID to a `Node` via the domain models' `to_node()` methods.

#### Scenario: Build path with two platform stops and intermediate blocks

- **WHEN** stops are `[P1, P2]` and blocks `[B1, B2]` connect them
- **THEN** the returned path is `[Node(P1, PLATFORM), Node(B1, BLOCK), Node(B2, BLOCK), Node(P2, PLATFORM)]`

#### Scenario: Build path starting or ending at a yard

- **WHEN** the first stop is a yard ID and the second is a platform
- **THEN** the yard is resolved as `Node(yard_id, YARD)` via `Station.to_node()`

### Requirement: RouteBuilder computes timetable from path

`RouteBuilder` SHALL compute a `list[TimetableEntry]` for the full path, using `Block.to_timetable_entry()` for block nodes and `Platform.to_timetable_entry()` / `Station.to_timetable_entry()` for stop nodes. Dwell times for stops SHALL be provided by the caller.

#### Scenario: Timetable with blocks and a platform dwell

- **WHEN** path is `[P1, B1, P2]`, start_time=0, B1 traversal=60s, P1 dwell=30s
- **THEN** P1 entry: arrival=0, departure=30; B1 entry: arrival=30, departure=90; P2 entry: arrival=90, departure=90

### Requirement: RouteBuilder validates stops exist

`RouteBuilder` SHALL validate that every stop ID references a known platform or yard before building the path. It SHALL raise `DomainError(ErrorCode.VALIDATION)` if any stop ID is not found.

#### Scenario: Unknown stop ID

- **WHEN** a stop references a node ID that is neither a platform nor a yard
- **THEN** a `DomainError` with `ErrorCode.VALIDATION` is raised

### Requirement: ServiceAppService delegates to RouteBuilder

`ServiceAppService._build_route` SHALL load domain objects (stations, connections, blocks) and delegate path construction and timetable computation to `RouteBuilder`. It SHALL NOT contain node-type mapping, timetable arithmetic, or stop validation logic.

#### Scenario: _build_route orchestrates without domain logic

- **WHEN** `_build_route` is called with stops and start_time
- **THEN** it loads data from repositories, calls `RouteBuilder`, and returns the path and timetable produced by `RouteBuilder`

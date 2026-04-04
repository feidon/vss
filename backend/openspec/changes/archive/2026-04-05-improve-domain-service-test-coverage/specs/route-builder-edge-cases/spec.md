## ADDED Requirements

### Requirement: RouteBuilder handles yard as first stop
`build_full_route` SHALL correctly compute route and timetable when the first stop is the Yard station.

#### Scenario: Route starting from Yard to P1A
- **WHEN** `build_full_route` is called with `stop_ids=[Y, P1A]` and `dwell_by_stop={Y: 0, P1A: 60}`
- **THEN** the route SHALL contain nodes `[Y, B1, P1A]` with correct types (YARD, BLOCK, PLATFORM)
- **AND** the timetable SHALL have 3 entries with continuous timing

### Requirement: RouteBuilder handles yard as last stop
`build_full_route` SHALL correctly compute route and timetable when the last stop is the Yard station.

#### Scenario: Route ending at Yard from P1A
- **WHEN** `build_full_route` is called with `stop_ids=[P1A, Y]` and `dwell_by_stop={P1A: 60}`
- **THEN** the route SHALL contain nodes `[P1A, B1, Y]`
- **AND** the last timetable entry SHALL be for the Yard node with YARD type

### Requirement: RouteBuilder timetable entries are continuous
Each timetable entry's departure SHALL equal the next entry's arrival, forming a continuous timeline.

#### Scenario: Three-stop route timing continuity
- **WHEN** `build_full_route` is called with `stop_ids=[P1A, P2A, P3A]` and `dwell_by_stop={P1A: 60, P2A: 120, P3A: 0}`
- **THEN** for every consecutive pair of entries, `entries[i].departure == entries[i+1].arrival` SHALL hold

### Requirement: RouteBuilder yard dwell computes correctly
When a yard stop has dwell time, the timetable entry SHALL have `departure = arrival + dwell`.

#### Scenario: Yard with dwell time
- **WHEN** `build_full_route` is called with Yard as a stop and `dwell_by_stop={Y: 300}`
- **THEN** the Yard's timetable entry SHALL have `departure = arrival + 300`

### Requirement: RouteBuilder handles four-stop route
`build_full_route` SHALL correctly build routes with 4+ stops, computing all intermediate blocks.

#### Scenario: Four-stop route node count
- **WHEN** `build_full_route` is called with `stop_ids=[P1A, P2A, P3A, P2B]`
- **THEN** the route SHALL contain the correct number of nodes (P1A, B3, B5, P2A, B6, B7, P3A, B10, B11, P2B = 10 nodes)
- **AND** the timetable SHALL have 10 entries

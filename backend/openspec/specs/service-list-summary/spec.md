## ADDED Requirements

### Requirement: Service list includes start time
The `GET /api/services` response SHALL include a `start_time` field (integer, epoch seconds) for each service, derived from the first timetable entry's arrival time.

#### Scenario: Service with a saved route
- **WHEN** a service has a non-empty timetable
- **THEN** `start_time` SHALL equal `timetable[0].arrival`

#### Scenario: Newly created service with no route
- **WHEN** a service has an empty timetable (no route saved yet)
- **THEN** `start_time` SHALL be `null`

### Requirement: Service list includes origin name
The `GET /api/services` response SHALL include an `origin_name` field (string) for each service, derived from the first node in the route.

#### Scenario: Service with a saved route
- **WHEN** a service has a non-empty route
- **THEN** `origin_name` SHALL equal the `name` of the first node in the route

#### Scenario: Newly created service with no route
- **WHEN** a service has an empty route
- **THEN** `origin_name` SHALL be `null`

### Requirement: Service list includes destination name
The `GET /api/services` response SHALL include a `destination_name` field (string) for each service, derived from the last stop node (platform or yard) in the route.

#### Scenario: Service with a saved route
- **WHEN** a service has a non-empty route containing platform or yard nodes
- **THEN** `destination_name` SHALL equal the `name` of the last node in the route whose type is not `block`

#### Scenario: Newly created service with no route
- **WHEN** a service has an empty route
- **THEN** `destination_name` SHALL be `null`

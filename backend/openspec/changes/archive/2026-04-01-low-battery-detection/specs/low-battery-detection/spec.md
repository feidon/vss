## ADDED Requirements

### Requirement: Vehicle battery cost per block traversal
The system SHALL deduct 1% battery per block traversed during a service. The battery level MUST NOT drop below the critical threshold of 30%.

#### Scenario: Service completes within battery budget
- **WHEN** a vehicle with 100% battery is assigned a service traversing 5 blocks
- **THEN** the vehicle's battery after the service is 95% and no conflict is raised

#### Scenario: Service drains battery below critical threshold
- **WHEN** a vehicle with 50% battery is assigned a service traversing 25 blocks
- **THEN** the system raises a `LowBatteryConflict` identifying the service that would cause the violation

#### Scenario: Battery exactly at critical threshold
- **WHEN** a vehicle's battery would be exactly 30% after traversing a service's blocks
- **THEN** no low-battery conflict is raised (30% is the boundary, below 30% triggers conflict)

### Requirement: Low battery conflicts included in service validation
The system SHALL detect low-battery conflicts as part of the existing `validate_service()` pipeline. Low-battery conflicts MUST be returned alongside vehicle, block, and interlocking conflicts.

#### Scenario: Route update with low battery
- **WHEN** a route update is submitted and the resulting schedule would drain a vehicle below 30%
- **THEN** the API returns 409 with a response body containing `low_battery_conflicts`

#### Scenario: No battery issue
- **WHEN** a route update is submitted and battery remains above 30% for all services
- **THEN** no low-battery conflicts appear in the response

### Requirement: Battery simulation across ordered services
The system SHALL simulate battery state across all services for a vehicle in chronological order (sorted by first timetable entry arrival time). The simulation starts at 100% battery.

#### Scenario: Multiple services consume cumulative battery
- **WHEN** a vehicle has two services — first traversing 10 blocks, second traversing 15 blocks — with no idle time between them
- **THEN** the battery after both services is 75% (100 - 10 - 15) and no conflict is raised

#### Scenario: Third service causes low battery after prior drain
- **WHEN** a vehicle has three services with cumulative block count exceeding 70
- **THEN** a `LowBatteryConflict` is raised for the service that crosses the 30% threshold

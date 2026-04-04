## ADDED Requirements

### Requirement: All HTTP errors from route updates produce user-visible feedback
The schedule editor SHALL handle all HTTP error statuses from the route update API call, not only 409. For 409 responses, conflict details SHALL be displayed. For all other errors, a generic error message SHALL be shown.

#### Scenario: 409 conflict response displays conflict alert
- **WHEN** the route update returns HTTP 409
- **THEN** the conflict response body SHALL be parsed and displayed in the conflict alert component (existing behavior)

#### Scenario: Non-409 error displays generic error message
- **WHEN** the route update returns a non-409 error (e.g., 400, 422, 500, network failure)
- **THEN** a user-visible error message SHALL be displayed (e.g., "Failed to update route. Please try again.")
- **AND** the error message SHALL be dismissible

#### Scenario: Error state clears on new submission
- **WHEN** the user submits a new route update
- **THEN** both the conflict signal and the error message signal SHALL be cleared before the request is made

### Requirement: Conflict alert renders all conflict types from the backend response
The conflict alert component SHALL render all four conflict types that the backend can return: vehicle conflicts, block conflicts, interlocking conflicts, and battery conflicts. No conflict type SHALL be silently omitted.

#### Scenario: Vehicle conflicts are displayed
- **WHEN** the conflict response contains vehicle_conflicts
- **THEN** each vehicle conflict SHALL be rendered showing the conflicting service IDs and reason

#### Scenario: Block conflicts are displayed
- **WHEN** the conflict response contains block_conflicts
- **THEN** each block conflict SHALL be rendered showing block ID, service IDs, and overlap time range

#### Scenario: Interlocking conflicts are displayed
- **WHEN** the conflict response contains interlocking_conflicts
- **THEN** each interlocking conflict SHALL be rendered showing group, block IDs, service IDs, and overlap time range

#### Scenario: Battery conflicts are displayed
- **WHEN** the conflict response contains battery_conflicts
- **THEN** each battery conflict SHALL be rendered showing type (low_battery or insufficient_charge) and service ID

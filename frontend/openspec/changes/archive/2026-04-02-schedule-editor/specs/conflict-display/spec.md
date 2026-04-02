## ADDED Requirements

### Requirement: Display conflict details on 409
When a route update returns HTTP 409, the system SHALL parse the `ConflictResponse` from `error.error.detail` and display each conflict type in a visible alert panel.

#### Scenario: Vehicle conflict displayed
- **WHEN** the 409 response contains a vehicle conflict with reason "Overlapping time windows"
- **THEN** the alert shows "Vehicle conflict: Overlapping time windows" with the involved service IDs

#### Scenario: Block conflict displayed
- **WHEN** the 409 response contains a block conflict for block B3
- **THEN** the alert shows the block name and the overlap time range

#### Scenario: Interlocking conflict displayed
- **WHEN** the 409 response contains an interlocking conflict for group 2
- **THEN** the alert shows the interlocking group number, involved blocks, and overlap time range

#### Scenario: Battery conflicts displayed
- **WHEN** the 409 response contains low_battery or insufficient_charge conflicts
- **THEN** the alert shows the affected service IDs with a description of the battery issue

### Requirement: Conflict alert is dismissable
The conflict alert panel SHALL be dismissable by the user, allowing them to adjust the route and resubmit.

#### Scenario: Dismiss conflict alert
- **WHEN** user clicks dismiss on the conflict alert
- **THEN** the alert is hidden and the route editor remains editable

### Requirement: Multiple conflict types shown together
When a 409 response contains multiple conflict types, the alert SHALL display all of them grouped by type.

#### Scenario: Mixed conflicts
- **WHEN** the 409 response contains both vehicle conflicts and block conflicts
- **THEN** the alert displays both groups with clear headings

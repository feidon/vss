## ADDED Requirements

### Requirement: Create a new service
The system SHALL provide a form with a name text input and a vehicle dropdown. On submit, it SHALL call `POST /services` and then open the route editor for the newly created service.

#### Scenario: Successful creation
- **WHEN** user enters name "S101", selects vehicle "V1", and submits
- **THEN** `POST /services` is called with `{ name: "S101", vehicle_id: "<v1-uuid>" }` and the route editor opens for the new service

#### Scenario: Validation — name required
- **WHEN** user attempts to submit with an empty name
- **THEN** the form shows a validation error and does not call the API

### Requirement: Edit service route with platform stops
The route editor SHALL display a stop picker where the user adds platform stops in order from a dropdown of available platforms (grouped by station). Each stop SHALL have an editable dwell_time field (default: 30 seconds). The user SHALL set a start_time via a datetime-local input.

#### Scenario: Add stops and submit route
- **WHEN** user adds platforms P1A and P2A as stops, sets dwell_time to 30 each, sets start_time, and submits
- **THEN** `PATCH /services/{id}/route` is called with `{ stops: [{ platform_id: "<p1a-uuid>", dwell_time: 30 }, { platform_id: "<p2a-uuid>", dwell_time: 30 }], start_time: <epoch> }`

#### Scenario: Remove a stop
- **WHEN** user removes a stop from the ordered list
- **THEN** the stop is removed and remaining stops maintain their order

#### Scenario: Validation — at least two stops required
- **WHEN** user attempts to submit with fewer than two stops
- **THEN** the form shows a validation error and does not call the API

### Requirement: Display current timetable after route update
After a successful route update, the system SHALL reload the service and display the computed timetable showing each node in the path with its arrival and departure times formatted as human-readable time strings.

#### Scenario: Timetable displayed after update
- **WHEN** route update succeeds
- **THEN** the service is reloaded via `GET /services/{id}` and the timetable is displayed with node name, arrival time, and departure time per row

### Requirement: Back to list navigation
The route editor SHALL provide a "Back to list" action that returns to the service list view.

#### Scenario: Return to list
- **WHEN** user clicks "Back to list" in the route editor
- **THEN** the service list is displayed with refreshed data

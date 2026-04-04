## ADDED Requirements

### Requirement: Editor populates stop queue from existing service route
When the user navigates to the editor for a service that already has a saved route, the stop queue SHALL be populated with the non-block nodes from the route, each with its correct dwell time derived from the timetable.

#### Scenario: Existing service with saved route
- **WHEN** user navigates to `/schedule/:id/edit` for a service with route `[P1A, B3, B5, P2A]` and timetable entries for each node
- **THEN** the stop queue displays `[P1A, P2A]` (blocks filtered out), each with dwell time = `departure - arrival` from the corresponding timetable entry

#### Scenario: Existing service with no route
- **WHEN** user navigates to `/schedule/:id/edit` for a service with an empty route
- **THEN** the stop queue is empty and the start time field is blank

### Requirement: Editor populates start time from existing service timetable
When the user navigates to the editor for a service that already has a saved timetable, the start time field SHALL be populated with the arrival time of the first timetable entry.

#### Scenario: Existing service with timetable
- **WHEN** user navigates to `/schedule/:id/edit` for a service with `timetable[0].arrival = 1700000000`
- **THEN** the start time datetime-local input displays the equivalent local datetime

### Requirement: Conflict alert displays on 409 route update response
When a route update returns HTTP 409, the editor SHALL display the `ConflictAlertComponent` with all conflict details from the response body.

#### Scenario: Route update triggers vehicle conflict
- **WHEN** user submits a route update and the API returns 409 with `vehicle_conflicts` containing one entry
- **THEN** the conflict alert renders showing the vehicle conflict with service IDs and reason

#### Scenario: Route update triggers multiple conflict types
- **WHEN** user submits a route update and the API returns 409 with `block_conflicts` and `battery_conflicts`
- **THEN** the conflict alert renders showing both block conflicts (with overlap times) and battery conflicts (with type)

#### Scenario: Conflict alert dismissal
- **WHEN** user clicks the dismiss button on the conflict alert
- **THEN** the conflict alert is removed from the page

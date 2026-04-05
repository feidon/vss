## ADDED Requirements

### Requirement: Conflict response is correctly parsed from 409 responses
The system SHALL extract conflict data from `err.error.detail` (not `err.error.detail.context`) when the backend returns a 409 status on route update.

#### Scenario: Backend returns 409 with conflict details
- **WHEN** `PATCH /api/services/{id}/route` returns 409 with `detail` containing `vehicle_conflicts`, `block_conflicts`, `interlocking_conflicts`, and `battery_conflicts`
- **THEN** the editor SHALL populate the `conflicts` signal with the parsed `ConflictResponse` and display the conflict details to the user

#### Scenario: Backend returns 409 with unexpected format
- **WHEN** `PATCH /api/services/{id}/route` returns 409 but `detail` does not contain the expected conflict fields
- **THEN** the editor SHALL display a generic error message "Conflict detected but response format was unexpected."

### Requirement: Auto-schedule button displays correct label
The auto-schedule button in the schedule list SHALL display "Auto-Generate Schedule" as its label text.

#### Scenario: Schedule list renders auto-schedule button
- **WHEN** the schedule list page loads
- **THEN** the auto-schedule button SHALL be visible with the label "Auto-Generate Schedule"

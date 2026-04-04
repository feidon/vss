## ADDED Requirements

### Requirement: Create service dialog with name, vehicle, and start time
The system SHALL provide a modal dialog for creating a new service. The dialog SHALL contain:
- A text input for the service name (required)
- A dropdown for selecting a vehicle (loaded from `GET /api/vehicles`)
- A datetime-local input for the start time (required)

On submit, the dialog SHALL call `POST /api/services` with the name and vehicle_id, then close and return the created service ID along with the start time.

#### Scenario: Successful creation
- **WHEN** user fills in name "S101", selects vehicle "V1", sets start time to "2025-01-01T08:00", and clicks Create
- **THEN** `POST /api/services` is called with `{ name: "S101", vehicle_id: "<v1-uuid>" }`, the dialog closes, and the app navigates to `/schedule/<new-id>/edit` with the start time passed as state

#### Scenario: Validation — all fields required
- **WHEN** user attempts to submit with an empty name or no vehicle selected or no start time
- **THEN** the dialog shows validation errors and does not call the API

#### Scenario: Cancel closes dialog
- **WHEN** user clicks Cancel or presses Escape
- **THEN** the dialog closes without creating a service

### Requirement: Vehicle list loading
The dialog SHALL load the vehicle list on open. While loading, the vehicle dropdown SHALL be disabled. If loading fails, an error message SHALL be displayed.

#### Scenario: Vehicles loaded successfully
- **WHEN** the dialog opens and `GET /api/vehicles` returns V1, V2, V3
- **THEN** the vehicle dropdown contains three options: V1, V2, V3

#### Scenario: Vehicle loading error
- **WHEN** `GET /api/vehicles` fails
- **THEN** the dialog shows an error message and the submit button is disabled

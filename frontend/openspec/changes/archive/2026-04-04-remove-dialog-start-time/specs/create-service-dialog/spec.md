## MODIFIED Requirements

### Requirement: Create service dialog with name and vehicle
The system SHALL provide a modal dialog for creating a new service. The dialog SHALL contain:
- A text input for the service name (required)
- A dropdown for selecting a vehicle (loaded from `GET /api/vehicles`)

On submit, the dialog SHALL call `POST /api/services` with the name and vehicle_id, then close and return the created service ID.

#### Scenario: Successful creation
- **WHEN** user fills in name "S101", selects vehicle "V1", and clicks Create
- **THEN** `POST /api/services` is called with `{ name: "S101", vehicle_id: "<v1-uuid>" }`, the dialog closes, and the app navigates to `/schedule/<new-id>/edit`

#### Scenario: Validation — name and vehicle required
- **WHEN** user attempts to submit with an empty name or no vehicle selected
- **THEN** the dialog shows validation errors and does not call the API

#### Scenario: Cancel closes dialog
- **WHEN** user clicks Cancel or presses Escape
- **THEN** the dialog closes without creating a service

## REMOVED Requirements

### Requirement: Start time collection in dialog
**Reason**: Start time is redundant — the route editor already has a start time input, and the dialog's start time was never consumed by downstream code.
**Migration**: Users set start time in the route editor after navigating to the editor page.

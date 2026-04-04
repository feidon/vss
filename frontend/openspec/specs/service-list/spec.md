## ADDED Requirements

### Requirement: Display all services in a table
The system SHALL display a table of all services showing: name, vehicle name, start time, origin, destination, and action buttons (Edit, Delete). The list SHALL be the main schedule page at `/schedule`. The origin and destination columns SHALL display the string name values returned by the `GET /api/services` response.

#### Scenario: Services loaded and displayed
- **WHEN** the schedule page loads
- **THEN** all services from `GET /api/services` are displayed in a table with name, vehicle, start time, origin, destination columns

#### Scenario: Origin and destination display correct string names
- **WHEN** the API returns a service with `origin: "P1A"` and `destination: "P2A"`
- **THEN** the origin column displays "P1A" and the destination column displays "P2A"

#### Scenario: Null origin or destination
- **WHEN** the API returns a service with `origin: null` or `destination: null`
- **THEN** the corresponding column displays "—" (em dash)

#### Scenario: Empty state
- **WHEN** no services exist
- **THEN** the table shows a message indicating no services have been created

### Requirement: Create service button
The schedule list SHALL display a "Create Service" button. Clicking it SHALL open the create-service dialog.

#### Scenario: Open create dialog
- **WHEN** user clicks the "Create Service" button
- **THEN** the create-service dialog opens

#### Scenario: After creation navigate to editor
- **WHEN** the create-service dialog completes successfully with a new service ID
- **THEN** the app navigates to `/schedule/<id>/edit`

### Requirement: Delete a service
The system SHALL allow deleting a service via a Delete button on each row. A confirmation prompt SHALL be shown before deletion.

#### Scenario: Delete with confirmation
- **WHEN** user clicks Delete on a service row and confirms
- **THEN** `DELETE /api/services/{id}` is called and the service is removed from the list

#### Scenario: Delete cancelled
- **WHEN** user clicks Delete but cancels the confirmation
- **THEN** no API call is made and the list remains unchanged

### Requirement: Navigate to route editing
The system SHALL allow navigating to the route editor for a service via an Edit button on each row.

#### Scenario: Edit button navigates to editor
- **WHEN** user clicks Edit on a service row
- **THEN** the app navigates to `/schedule/<id>/edit`

### Requirement: Vehicle name resolution
The service list SHALL display the vehicle name (e.g., "V1") rather than the vehicle UUID. Vehicle name SHALL come from the `vehicle_name` field in the service list response.

#### Scenario: Vehicle name displayed
- **WHEN** a service has `vehicle_name: "V1"`
- **THEN** the table shows "V1" in the vehicle column

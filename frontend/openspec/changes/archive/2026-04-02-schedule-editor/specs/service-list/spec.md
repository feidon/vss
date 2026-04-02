## ADDED Requirements

### Requirement: Display all services in a table
The system SHALL display a table of all services showing: name, vehicle name, number of stops (platform nodes in path), and action buttons (Edit, Delete).

#### Scenario: Services loaded and displayed
- **WHEN** the editor page loads
- **THEN** all services from `GET /services` are displayed in a table with name, vehicle, and stop count columns

#### Scenario: Empty state
- **WHEN** no services exist
- **THEN** the table shows a message indicating no services have been created

### Requirement: Delete a service
The system SHALL allow deleting a service via a Delete button on each row. A confirmation prompt SHALL be shown before deletion.

#### Scenario: Delete with confirmation
- **WHEN** user clicks Delete on a service row and confirms
- **THEN** `DELETE /services/{id}` is called and the service is removed from the list

#### Scenario: Delete cancelled
- **WHEN** user clicks Delete but cancels the confirmation
- **THEN** no API call is made and the list remains unchanged

### Requirement: Navigate to route editing
The system SHALL allow navigating to the route editor for a service via an Edit button on each row.

#### Scenario: Edit button shows route editor
- **WHEN** user clicks Edit on a service row
- **THEN** the route editor is displayed for that service with its current path and timetable

### Requirement: Vehicle name resolution
The service list SHALL display the vehicle name (e.g., "V1") rather than the vehicle UUID. Vehicle data SHALL be loaded from `GET /graph`.

#### Scenario: Vehicle name displayed
- **WHEN** a service has `vehicle_id: "some-uuid"` and the graph contains `{ id: "some-uuid", name: "V1" }`
- **THEN** the table shows "V1" in the vehicle column

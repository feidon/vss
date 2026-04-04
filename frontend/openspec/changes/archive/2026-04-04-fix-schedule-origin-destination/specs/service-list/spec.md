## MODIFIED Requirements

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

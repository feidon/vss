## ADDED Requirements

### Requirement: Display all services in a table
The system SHALL display all services returned by `GET /services` in a table with columns: service name, vehicle name, and number of platform stops.

#### Scenario: Services exist
- **WHEN** the viewer page loads and the API returns one or more services
- **THEN** the system displays a table row per service showing the service name, resolved vehicle name (not UUID), and the count of platform nodes in the service path

#### Scenario: No services exist
- **WHEN** the viewer page loads and the API returns an empty list
- **THEN** the system displays an empty-state message indicating no services are scheduled

### Requirement: Resolve vehicle UUIDs to display names
The system SHALL resolve vehicle UUIDs to human-readable vehicle names using vehicle data from `GET /graph`.

#### Scenario: Vehicle name resolution
- **WHEN** a service has a `vehicle_id` that matches a vehicle in the graph response
- **THEN** the system displays the vehicle's `name` property instead of its UUID

#### Scenario: Unknown vehicle ID
- **WHEN** a service has a `vehicle_id` that does not match any vehicle in the graph response
- **THEN** the system displays the raw UUID as a fallback

### Requirement: Filter services by vehicle
The system SHALL provide a vehicle filter dropdown that limits the displayed services to those assigned to the selected vehicle.

#### Scenario: Filter by specific vehicle
- **WHEN** the user selects a vehicle from the filter dropdown
- **THEN** only services assigned to that vehicle are displayed in the table

#### Scenario: Show all services
- **WHEN** the user selects the "All vehicles" option (default)
- **THEN** all services are displayed regardless of vehicle assignment

### Requirement: Group services by vehicle
The system SHALL provide a toggle to group services by their assigned vehicle, displaying vehicle name as a group header.

#### Scenario: Enable grouping
- **WHEN** the user activates the group-by-vehicle toggle
- **THEN** services are organized under vehicle name headers, with each group listing only services for that vehicle

#### Scenario: Disable grouping
- **WHEN** the user deactivates the group-by-vehicle toggle
- **THEN** services are displayed in a flat list without grouping

### Requirement: Select a service to view timetable
The system SHALL allow the user to select a service from the list to view its timetable detail.

#### Scenario: Select a service
- **WHEN** the user clicks on a service row in the table
- **THEN** the timetable detail view for that service is displayed

#### Scenario: Deselect / return to list
- **WHEN** the user clicks a "Back to list" action from the timetable detail view
- **THEN** the timetable detail is hidden and the full service list is shown again

## ADDED Requirements

### Requirement: Vehicle list section on config page
The config page SHALL display a "Vehicles" section that lists all vehicles fetched from `GET /api/vehicles`. The section SHALL appear below the block configuration table.

#### Scenario: Vehicles are loaded and displayed
- **WHEN** the user navigates to the config page
- **THEN** the system SHALL fetch vehicles from `GET /api/vehicles` and display them in a table with columns: Name

#### Scenario: Vehicles are sorted by name
- **WHEN** vehicles are loaded
- **THEN** the system SHALL sort vehicles alphabetically by name (natural alphanumeric order, e.g., V1, V2, V3, V10)

#### Scenario: Loading state
- **WHEN** vehicles are being fetched from the API
- **THEN** the system SHALL display a loading indicator until the data is available

#### Scenario: API error
- **WHEN** the vehicle API call fails
- **THEN** the system SHALL display an error message using the existing error alert component

### Requirement: Block group column centering
The block configuration table's group column SHALL horizontally center its content, including the "-" placeholder for ungrouped blocks.

#### Scenario: Ungrouped block displays centered dash
- **WHEN** a block has `group === 0`
- **THEN** the "-" text SHALL be horizontally centered within the group column cell

#### Scenario: Grouped block badge remains centered
- **WHEN** a block has `group > 0`
- **THEN** the group badge SHALL remain horizontally centered within the group column cell

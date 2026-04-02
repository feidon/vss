## ADDED Requirements

### Requirement: Display timetable entries in order
The system SHALL display the timetable of a selected service as an ordered table with columns: order, node name, node type, arrival time, and departure time.

#### Scenario: Service with timetable entries
- **WHEN** the user selects a service that has timetable entries
- **THEN** the system displays each timetable entry sorted by `order`, showing the node name resolved from the service path, the node type (block/platform/yard), and the arrival and departure times

#### Scenario: Service with no timetable entries
- **WHEN** the user selects a service that has an empty timetable
- **THEN** the system displays a message indicating the service has no timetable (route not yet configured)

### Requirement: Format epoch timestamps as human-readable time
The system SHALL display arrival and departure times as `HH:mm:ss` formatted strings rather than raw epoch seconds.

#### Scenario: Valid epoch timestamp
- **WHEN** a timetable entry has arrival or departure as epoch seconds (e.g., 1700000000)
- **THEN** the system displays the time formatted as `HH:mm:ss` in the local timezone

#### Scenario: Null or zero timestamp
- **WHEN** a timetable entry has an arrival or departure value of 0
- **THEN** the system displays a dash (`—`) as a placeholder

### Requirement: Display service header information
The system SHALL display the selected service's name and assigned vehicle name above the timetable.

#### Scenario: Service header
- **WHEN** a service is selected for timetable viewing
- **THEN** the system displays the service name and vehicle name as a header above the timetable table

### Requirement: Highlight platform stops in timetable
The system SHALL visually distinguish platform stops from block/yard nodes in the timetable display.

#### Scenario: Platform node in timetable
- **WHEN** a timetable entry corresponds to a node of type `platform`
- **THEN** the row is visually highlighted (e.g., bolder text or background color) to distinguish it from transit blocks

#### Scenario: Non-platform node in timetable
- **WHEN** a timetable entry corresponds to a node of type `block` or `yard`
- **THEN** the row is displayed in the default style without highlighting

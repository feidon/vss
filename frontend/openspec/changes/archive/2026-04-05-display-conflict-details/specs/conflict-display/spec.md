## MODIFIED Requirements

### Requirement: Display conflict details on 409
When a route update returns HTTP 409, the system SHALL parse the `ConflictResponse` from `error.error.detail` and display each conflict type in a visible alert panel. All entity references (blocks, vehicles, services) SHALL be displayed using human-readable names resolved from the graph data, falling back to raw IDs if resolution fails.

#### Scenario: Block conflict displays block name
- **WHEN** the 409 response contains a block conflict with `block_id` referencing a block named "B3"
- **THEN** the alert SHALL display "B3" instead of the raw UUID

#### Scenario: Interlocking conflict displays block names
- **WHEN** the 409 response contains an interlocking conflict with `block_a_id` referencing "B7" and `block_b_id` referencing "B8"
- **THEN** the alert SHALL display "B7" and "B8" instead of raw UUIDs

#### Scenario: Vehicle conflict displays vehicle name
- **WHEN** the 409 response contains a vehicle conflict with `vehicle_id` referencing a vehicle named "V1"
- **THEN** the alert SHALL display "V1" instead of the raw UUID

#### Scenario: Service IDs display as service names
- **WHEN** the 409 response contains any conflict with `service_a_id: 101` and `service_b_id: 102`
- **THEN** the alert SHALL display "S101" and "S102"

#### Scenario: Unknown ID falls back to raw value
- **WHEN** the 409 response contains a block_id that does not exist in the graph nodes
- **THEN** the alert SHALL display the raw UUID as a fallback

### Requirement: Conflict alert receives graph data for name resolution
The `ConflictAlertComponent` SHALL accept a `graph` input of type `GraphResponse`. It SHALL use `graph.nodes` to resolve block/platform/yard IDs to names, and `graph.vehicles` to resolve vehicle IDs to names.

#### Scenario: Graph input is provided by parent
- **WHEN** the `ScheduleEditorComponent` renders the conflict alert
- **THEN** it SHALL pass the current service's `graph` to the conflict alert component

## MODIFIED Requirements

### Requirement: Node types
The system SHALL define node types as a discriminated union by `type` field. All node types SHALL include `x: number` and `y: number` fields for layout coordinates (default 0).

- `BlockNode`: `{ type: 'block', id, name, group, traversal_time_seconds, x, y }`
- `PlatformNode`: `{ type: 'platform', id, name, x, y }`
- `YardNode`: `{ type: 'yard', id, name, x, y }`

#### Scenario: Block node includes coordinates
- **WHEN** the backend returns a block node with `x: 100.0` and `y: 200.0`
- **THEN** the frontend `BlockNode` type includes those values

#### Scenario: Default coordinates
- **WHEN** the backend returns a node without explicit coordinates
- **THEN** the node has `x: 0` and `y: 0`

### Requirement: Service list response type
The system SHALL define `ServiceResponse` for `GET /services` containing only `id: number`, `name: string`, `vehicle_id: string`. It SHALL NOT include `path`, `timetable`, or `graph` fields.

#### Scenario: List response shape
- **WHEN** `GET /services` returns `[{ "id": 1, "name": "S1", "vehicle_id": "uuid" }]`
- **THEN** the response maps to `ServiceResponse` with only those three fields

### Requirement: Service detail response type
The system SHALL define `ServiceDetailResponse` for `GET /services/{id}` containing `id`, `name`, `vehicle_id`, `route: Node[]`, `timetable: TimetableEntry[]`, and `graph: GraphResponse`.

#### Scenario: Detail response includes graph
- **WHEN** `GET /services/1` returns a response with `graph`, `route`, and `timetable`
- **THEN** the response maps to `ServiceDetailResponse` with all fields including the nested `GraphResponse`

### Requirement: Route stop request uses node_id
The system SHALL define `StopRequest` with field `node_id: string` (not `platform_id`), matching the backend's `RouteStopInput` schema.

#### Scenario: Route update sends node_id
- **WHEN** the user submits a route with stops
- **THEN** the request body contains `{ stops: [{ node_id: "uuid", dwell_time: 30 }], start_time: ... }`

### Requirement: InsufficientChargeConflict shape
The system SHALL define `InsufficientChargeConflict` with a single `service_id: number` field, matching the backend's 409 response.

#### Scenario: Insufficient charge conflict received
- **WHEN** a 409 response includes `insufficient_charge_conflicts: [{ "service_id": 1 }]`
- **THEN** the frontend parses it as `InsufficientChargeConflict` with `service_id: 1`

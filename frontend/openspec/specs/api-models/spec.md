### Requirement: Node discriminated union types
The system SHALL define a TypeScript discriminated union for Node with three variants: `BlockNode` (type: "block"), `PlatformNode` (type: "platform"), and `YardNode` (type: "yard"). `BlockNode` SHALL include `group: number` and `traversal_time_seconds: number`. All variants SHALL include `id: string` and `name: string`.

#### Scenario: Type narrowing on node type
- **WHEN** code checks `node.type === 'block'`
- **THEN** TypeScript narrows to `BlockNode` with `group` and `traversal_time_seconds` accessible

### Requirement: Block types
The system SHALL define `BlockResponse` matching `{ id: string, name: string, group: number, traversal_time_seconds: number }` and `UpdateBlockRequest` matching `{ traversal_time_seconds: number }`.

#### Scenario: Block response shape
- **WHEN** `GET /blocks` response is typed as `BlockResponse[]`
- **THEN** each element has `id`, `name`, `group`, and `traversal_time_seconds` fields

### Requirement: Service types
The system SHALL define `ServiceResponse` matching `{ id: number, name: string, vehicle_id: string, path: Node[], timetable: TimetableEntry[] }`, `CreateServiceRequest` matching `{ name: string, vehicle_id: string }`, and `UpdateRouteRequest` matching `{ stops: StopRequest[], start_time: number }` where `StopRequest` is `{ platform_id: string, dwell_time: number }`.

#### Scenario: Service response with timetable
- **WHEN** `GET /services/{id}` response is typed as `ServiceResponse`
- **THEN** `timetable` is an array of `TimetableEntry` with `order`, `node_id`, `arrival`, `departure`

### Requirement: Timetable entry type
The system SHALL define `TimetableEntry` matching `{ order: number, node_id: string, arrival: number, departure: number }` where arrival and departure are Unix epoch seconds.

#### Scenario: Timetable entry fields
- **WHEN** a `TimetableEntry` is accessed
- **THEN** `arrival` and `departure` are `number` (epoch seconds), not `Date`

### Requirement: Graph response types
The system SHALL define `GraphResponse` matching `{ nodes: Node[], connections: Connection[], stations: Station[], vehicles: Vehicle[] }` where `Connection` is `{ from_id: string, to_id: string }`, `Station` is `{ id: string, name: string, is_yard: boolean, platform_ids: string[] }`, and `Vehicle` is `{ id: string, name: string }`.

#### Scenario: Graph response includes all network data
- **WHEN** `GET /graph` response is typed as `GraphResponse`
- **THEN** it contains nodes, connections, stations, and vehicles arrays

### Requirement: Conflict response types
The system SHALL define `ConflictResponse` matching the 409 response shape with fields: `message: string`, `vehicle_conflicts: VehicleConflict[]`, `block_conflicts: BlockConflict[]`, `interlocking_conflicts: InterlockingConflict[]`, `low_battery_conflicts: LowBatteryConflict[]`, `insufficient_charge_conflicts: InsufficientChargeConflict[]`.

#### Scenario: Conflict type discrimination
- **WHEN** a 409 response is parsed as `ConflictResponse`
- **THEN** each conflict array is typed with its specific fields (e.g., `BlockConflict` has `block_id`, `overlap_start`, `overlap_end`)

### Requirement: ID response types
The system SHALL define `BlockIdResponse` matching `{ id: string }` and `ServiceIdResponse` matching `{ id: number }`.

#### Scenario: Mutation response typing
- **WHEN** `POST /services` response is typed as `ServiceIdResponse`
- **THEN** `id` is `number`

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

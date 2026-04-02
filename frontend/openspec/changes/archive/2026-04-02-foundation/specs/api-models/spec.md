## ADDED Requirements

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

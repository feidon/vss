## ADDED Requirements

### Requirement: Service detail response includes graph data
The `GET /services/{id}` endpoint SHALL return the full track network graph embedded in the response alongside the existing service fields. The graph data SHALL include nodes (blocks, platforms, yard), connections, stations, and vehicles.

#### Scenario: Retrieve service detail with graph
- **WHEN** a client sends `GET /services/{id}` with a valid service ID
- **THEN** the response SHALL contain the service fields (id, name, vehicle_id, path, timetable) AND a `graph` object containing `nodes`, `connections`, `stations`, and `vehicles`

#### Scenario: Graph data is complete
- **WHEN** a client retrieves a service detail
- **THEN** the `graph.nodes` array SHALL contain all blocks, platforms, and yard nodes in the network with their layout coordinates (x, y)
- **AND** the `graph.connections` array SHALL contain all directed edges in the track network
- **AND** the `graph.stations` array SHALL contain all stations with their platform IDs
- **AND** the `graph.vehicles` array SHALL contain all vehicles

#### Scenario: Service not found
- **WHEN** a client sends `GET /services/{id}` with a non-existent service ID
- **THEN** the endpoint SHALL return HTTP 404

### Requirement: Service list does not include graph data
The `GET /services` endpoint SHALL NOT include graph data in its response. The list response shape SHALL remain unchanged.

#### Scenario: List services returns summary only
- **WHEN** a client sends `GET /services`
- **THEN** each item in the response array SHALL contain only id, name, vehicle_id, path, and timetable
- **AND** no `graph` field SHALL be present

### Requirement: Standalone graph endpoint is removed
The `GET /graph` endpoint SHALL be removed. Clients MUST use `GET /services/{id}` to obtain graph data.

#### Scenario: Graph endpoint returns 404
- **WHEN** a client sends `GET /graph`
- **THEN** the server SHALL return HTTP 404 (or equivalent "not found" behavior since the route no longer exists)

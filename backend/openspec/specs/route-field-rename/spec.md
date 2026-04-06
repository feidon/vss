## ADDED Requirements

### Requirement: Service entity uses `route` field name
The Service entity SHALL store its complete traversal sequence (list of Nodes) in a field named `route` instead of `path`.

#### Scenario: Service created with route field
- **WHEN** a Service is constructed with a list of Nodes
- **THEN** the Nodes SHALL be accessible via `service.route`
- **AND** there SHALL be no `path` attribute on Service

#### Scenario: Service.update_route uses route parameter
- **WHEN** `Service.update_route()` is called with a new list of Nodes and timetable
- **THEN** `service.route` SHALL be updated with the new Nodes
- **AND** the parameter name in `update_route()` SHALL be `route` (not `path`)

### Requirement: Validation messages reference `route`
Domain validation error messages SHALL reference "route" instead of "path".

#### Scenario: Entry references node not in route
- **WHEN** a TimetableEntry references a node_id that is not present in the service's route
- **THEN** the error message SHALL read "Entry references node {id} not in route"

#### Scenario: Empty route validation
- **WHEN** an empty list of Nodes is passed to route validation
- **THEN** the error message SHALL read "Route must contain at least one node"

#### Scenario: Route connectivity validation
- **WHEN** consecutive nodes in the route have no connection
- **THEN** the error message SHALL read "No connection: {from_id} -> {to_id}"

### Requirement: API responses use `route` field
All API response schemas SHALL use `route` instead of `path` for the service's traversal sequence.

#### Scenario: Service detail response contains route field
- **WHEN** `GET /services/{id}` returns a service detail
- **THEN** the JSON response SHALL contain a `route` key (not `path`) with the list of nodes

### Requirement: Database column named `route`
The services table in PostgreSQL SHALL store the traversal sequence in a JSONB column named `route`.

#### Scenario: Service persisted to database
- **WHEN** a Service is saved via the repository
- **THEN** the traversal sequence SHALL be stored in the `route` column of the `services` table

#### Scenario: Service loaded from database
- **WHEN** a Service is loaded from the database
- **THEN** the repository SHALL read from the `route` column and map it to `Service.route`

### Requirement: Repository mappers use `route` key
Both in-memory and PostgreSQL repository implementations SHALL use `route` as the field/key name in their mapping logic.

#### Scenario: PostgreSQL mapper serializes route
- **WHEN** the PostgreSQL repository converts a Service to a table row
- **THEN** the JSONB data SHALL be keyed under `route`

#### Scenario: PostgreSQL mapper deserializes route
- **WHEN** the PostgreSQL repository converts a table row to a Service entity
- **THEN** it SHALL read from `row["route"]` and pass it as the `route` kwarg to Service

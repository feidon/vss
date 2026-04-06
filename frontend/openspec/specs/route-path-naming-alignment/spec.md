### Requirement: Components use 'route' field name
All frontend components referencing a service's ordered list of nodes SHALL use the field name `route` (matching the backend's `ServiceDetailResponse.route`), not `path`.

#### Scenario: Service list shows platform count from route
- **WHEN** the service list component counts platform stops
- **THEN** it reads from `service.route`, not `service.path`

#### Scenario: Timetable detail resolves node names from route
- **WHEN** the timetable detail component looks up a node by ID
- **THEN** it searches `service.route`, not `service.path`

#### Scenario: Route editor submit uses node_id
- **WHEN** the route editor emits a submitted event with stops
- **THEN** each stop object contains `node_id` (not `platform_id`) and `dwell_time`

### Requirement: CLAUDE.md documents actual API
The frontend `CLAUDE.md` SHALL accurately list the available backend endpoints:
- Remove `GET /graph` and `GET /blocks/{id}` (do not exist)
- Add `GET /vehicles` (list all vehicles)
- Update `ServiceResponse` and route update request schemas to match actual backend

#### Scenario: CLAUDE.md reflects current API
- **WHEN** a developer reads the CLAUDE.md API table
- **THEN** every listed endpoint exists in the backend and response schemas match actual responses

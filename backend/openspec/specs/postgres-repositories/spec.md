## ADDED Requirements

### Requirement: Block repository persists blocks to PostgreSQL
The system SHALL implement `PostgresBlockRepository` using SQLAlchemy Core queries against `blocks_table`. It SHALL translate between `Block` domain entities and database rows via `_to_entity()` / `_to_table()` methods. `save()` SHALL use upsert (INSERT ON CONFLICT DO UPDATE).

#### Scenario: Find all blocks
- **WHEN** `find_all()` is called and blocks exist in the database
- **THEN** all blocks are returned as `Block` domain entities with correct id, name, group, and traversal_time_seconds

#### Scenario: Find block by ID
- **WHEN** `find_by_id(id)` is called with an existing block's UUID
- **THEN** the matching `Block` entity is returned

#### Scenario: Find block by ID not found
- **WHEN** `find_by_id(id)` is called with a non-existent UUID
- **THEN** `None` is returned

#### Scenario: Find blocks by IDs
- **WHEN** `find_by_ids(ids)` is called with a set of UUIDs
- **THEN** only blocks matching those UUIDs are returned

#### Scenario: Save new block (insert)
- **WHEN** `save(block)` is called with a block whose ID does not exist in the database
- **THEN** a new row is inserted into `blocks_table`

#### Scenario: Save existing block (update)
- **WHEN** `save(block)` is called with a block whose ID already exists in the database
- **THEN** the existing row is updated with the new field values

### Requirement: Vehicle repository reads vehicles from PostgreSQL
The system SHALL implement `PostgresVehicleRepository` using SQLAlchemy Core queries against `vehicles_table`. Vehicle is read-only reference data (no `save()` method in the interface).

#### Scenario: Find all vehicles
- **WHEN** `find_all()` is called
- **THEN** all vehicles are returned as `Vehicle` domain entities with correct id and name

#### Scenario: Find vehicle by ID
- **WHEN** `find_by_id(id)` is called with an existing vehicle's UUID
- **THEN** the matching `Vehicle` entity is returned

#### Scenario: Find vehicle by ID not found
- **WHEN** `find_by_id(id)` is called with a non-existent UUID
- **THEN** `None` is returned

### Requirement: Station repository loads stations with platforms from PostgreSQL
The system SHALL implement `PostgresStationRepository` using a LEFT JOIN between `stations_table` and `platforms_table`. It SHALL group joined rows into `Station` aggregates with their `Platform` children. Domain entities SHALL have zero SQLAlchemy imports.

#### Scenario: Find all stations with platforms
- **WHEN** `find_all()` is called
- **THEN** all stations are returned, each with their associated platforms populated

#### Scenario: Find station by ID with platforms
- **WHEN** `find_by_id(id)` is called with an existing station's UUID
- **THEN** the station is returned with its platforms populated

#### Scenario: Station with no platforms
- **WHEN** `find_by_id(id)` is called for a station that has no platforms (e.g., Yard)
- **THEN** the station is returned with an empty platforms list

#### Scenario: Find station by ID not found
- **WHEN** `find_by_id(id)` is called with a non-existent UUID
- **THEN** `None` is returned

### Requirement: Service repository persists services with JSONB columns to PostgreSQL
The system SHALL implement `PostgresServiceRepository` using SQLAlchemy Core queries against `services_table`. `path` and `timetable` fields SHALL be serialized to JSONB on save and deserialized to domain value objects on load. New services (id=None) SHALL receive an autoincremented ID from PostgreSQL via RETURNING.

#### Scenario: Save new service and get generated ID
- **WHEN** `save(service)` is called with a service where `id is None`
- **THEN** the service is inserted and its `id` field is set to the database-generated autoincrement value

#### Scenario: Save existing service (update)
- **WHEN** `save(service)` is called with a service that has an existing ID
- **THEN** the existing row is updated including the JSONB path and timetable columns

#### Scenario: Find service by ID with deserialized path and timetable
- **WHEN** `find_by_id(id)` is called for an existing service
- **THEN** the service is returned with `path` as `list[Node]` and `timetable` as `list[TimetableEntry]`

#### Scenario: Find services by vehicle ID
- **WHEN** `find_by_vehicle_id(vehicle_id)` is called
- **THEN** only services assigned to that vehicle are returned

#### Scenario: Delete service
- **WHEN** `delete(id)` is called with an existing service ID
- **THEN** the row is removed from the database

#### Scenario: Delete non-existent service
- **WHEN** `delete(id)` is called with a non-existent ID
- **THEN** no error is raised (idempotent)

### Requirement: Connection repository reads node connections from PostgreSQL
The system SHALL implement `PostgresConnectionRepository` using SQLAlchemy Core queries against `node_connections_table`. Connections are read-only reference data.

#### Scenario: Find all connections
- **WHEN** `find_all()` is called
- **THEN** all connections are returned as a `frozenset[NodeConnection]`

### Requirement: Domain entities have zero SQLAlchemy imports
All repository implementations SHALL use manual `_to_entity()` and `_to_table()` methods. Domain model files SHALL NOT import any SQLAlchemy module. The translation boundary is strictly at the repository layer.

Production source code (`api/`, `application/`, `main.py`) SHALL NOT import from `infra.memory`. The `infra/memory/` module remains available exclusively for test usage.

#### Scenario: Domain models are pure dataclasses
- **WHEN** the domain model source files are inspected
- **THEN** they contain no imports from `sqlalchemy` or any SQLAlchemy sub-package

#### Scenario: Production code does not reference in-memory adapters
- **WHEN** `api/dependencies.py` is inspected
- **THEN** it imports only from `infra.postgres`, not from `infra.memory`

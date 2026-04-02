## MODIFIED Requirements

### Requirement: Domain entities have zero SQLAlchemy imports
All repository implementations SHALL use manual `_to_entity()` and `_to_table()` methods. Domain model files SHALL NOT import any SQLAlchemy module. The translation boundary is strictly at the repository layer.

Production source code (`api/`, `application/`, `main.py`) SHALL NOT import from `infra.memory`. The `infra/memory/` module remains available exclusively for test usage.

#### Scenario: Domain models are pure dataclasses
- **WHEN** the domain model source files are inspected
- **THEN** they contain no imports from `sqlalchemy` or any SQLAlchemy sub-package

#### Scenario: Production code does not reference in-memory adapters
- **WHEN** `api/dependencies.py` is inspected
- **THEN** it imports only from `infra.postgres`, not from `infra.memory`

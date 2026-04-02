## ADDED Requirements

### Requirement: Production DI always wires PostgreSQL repositories
The `api/dependencies.py` module SHALL unconditionally define all `get_*_repo()` dependency providers to return PostgreSQL repository instances. There SHALL be no environment-variable branching or in-memory fallback in the DI container.

#### Scenario: Application starts with database configured
- **WHEN** the FastAPI application starts with a valid PostgreSQL connection
- **THEN** all repository dependency providers return PostgreSQL implementations with an injected `AsyncSession`

#### Scenario: No in-memory imports in dependencies module
- **WHEN** `api/dependencies.py` source code is inspected
- **THEN** it contains no imports from `infra.memory` and no imports from `infra.seed`

### Requirement: In-memory repos are only instantiated in test code
In-memory repository implementations SHALL only be imported and instantiated within the `tests/` directory. Production source code (`api/`, `application/`, `main.py`) SHALL NOT import from `infra.memory`.

#### Scenario: Production modules do not import in-memory repos
- **WHEN** source files in `api/`, `application/`, and `main.py` are inspected
- **THEN** none of them contain imports from `infra.memory`

#### Scenario: Test code uses in-memory repos as fixtures
- **WHEN** application-level tests run
- **THEN** they construct in-memory repository instances directly in test fixtures (not via the DI container)

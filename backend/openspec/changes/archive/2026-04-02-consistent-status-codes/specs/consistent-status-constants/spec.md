## ADDED Requirements

### Requirement: All HTTP status codes use starlette.status constants
The codebase SHALL use named constants from `starlette.status` (e.g., `HTTP_200_OK`, `HTTP_404_NOT_FOUND`) for all HTTP status code references. Raw integer status codes (e.g., `200`, `404`) SHALL NOT be used.

#### Scenario: Error handler uses status constants
- **WHEN** `api/error_handler.py` maps domain error codes to HTTP status codes
- **THEN** the `STATUS_MAP` values SHALL be `starlette.status` constants (`HTTP_404_NOT_FOUND`, `HTTP_400_BAD_REQUEST`, `HTTP_409_CONFLICT`, `HTTP_422_UNPROCESSABLE_ENTITY`)

#### Scenario: Test assertions use status constants
- **WHEN** an API test asserts a response status code
- **THEN** the assertion SHALL compare against a `starlette.status` constant (e.g., `assert response.status_code == HTTP_200_OK`)

#### Scenario: Route decorators use status constants
- **WHEN** a FastAPI route decorator specifies a non-default status code
- **THEN** it SHALL use a `starlette.status` constant (already the case for `api/service/routes.py`)

### Requirement: Import from starlette.status, not fastapi.status
All status constant imports SHALL use `from starlette.status import HTTP_...`. The `fastapi.status` re-export SHALL NOT be used.

#### Scenario: Consistent import source
- **WHEN** a file needs HTTP status constants
- **THEN** the import statement SHALL be `from starlette.status import HTTP_200_OK, ...`

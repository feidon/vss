## ADDED Requirements

### Requirement: DomainError with ErrorCode enum
The system SHALL define a single `DomainError` exception class in `domain/error.py` with an `ErrorCode` enum. All domain and application layer errors that represent business rule violations or entity lookup failures SHALL raise `DomainError` with the appropriate code.

Error codes:
- `NOT_FOUND` — entity does not exist
- `VALIDATION` — invalid input or business rule violation
- `CONFLICT` — scheduling conflict detected
- `NO_ROUTE` — no path exists between stops

#### Scenario: Domain model raises DomainError for validation failure
- **WHEN** a domain entity or value object receives invalid input (e.g., negative traversal time, empty service name)
- **THEN** a `DomainError` with `ErrorCode.VALIDATION` SHALL be raised with a descriptive message

#### Scenario: Application service raises DomainError for not found
- **WHEN** an application service cannot find a requested entity (service, block, vehicle, stop)
- **THEN** a `DomainError` with `ErrorCode.NOT_FOUND` SHALL be raised

#### Scenario: Domain service raises DomainError for no route
- **WHEN** the route finder cannot find a path between two stops
- **THEN** a `DomainError` with `ErrorCode.NO_ROUTE` SHALL be raised

### Requirement: ConflictError as DomainError subclass
`ConflictError` SHALL be a subclass of `DomainError` with `ErrorCode.CONFLICT` and SHALL carry the `ServiceConflicts` domain object as structured detail.

#### Scenario: Conflict detection raises ConflictError
- **WHEN** `update_service_route` detects scheduling conflicts
- **THEN** a `ConflictError` SHALL be raised containing the `ServiceConflicts` object

### Requirement: Unified FastAPI exception handler
The system SHALL register a single `DomainError` exception handler in FastAPI that maps error codes to HTTP status codes:

| ErrorCode    | HTTP Status |
|-------------|-------------|
| NOT_FOUND   | 404         |
| VALIDATION  | 400         |
| CONFLICT    | 409         |
| NO_ROUTE    | 422         |

The error handler's response shapes SHALL be documented in OpenAPI via Pydantic response models declared on route decorators. The `ErrorResponse` and `ConflictDetailResponse` models SHALL match the shapes produced by the handler.

#### Scenario: NOT_FOUND error returns 404
- **WHEN** a request triggers a `DomainError` with `ErrorCode.NOT_FOUND`
- **THEN** the API SHALL return HTTP 404 with `{"detail": "<error message>"}`

#### Scenario: VALIDATION error returns 400
- **WHEN** a request triggers a `DomainError` with `ErrorCode.VALIDATION`
- **THEN** the API SHALL return HTTP 400 with `{"detail": "<error message>"}`

#### Scenario: CONFLICT error returns 409 with structured detail
- **WHEN** a request triggers a `ConflictError`
- **THEN** the API SHALL return HTTP 409 with the existing structured conflict detail format (vehicle_conflicts, block_conflicts, interlocking_conflicts, battery_conflicts)

#### Scenario: NO_ROUTE error returns 422
- **WHEN** a request triggers a `DomainError` with `ErrorCode.NO_ROUTE`
- **THEN** the API SHALL return HTTP 422 with `{"detail": "<error message>"}`

#### Scenario: Error response shapes are visible in Swagger
- **WHEN** a developer opens Swagger UI
- **THEN** all routes that can produce `DomainError` SHALL show the applicable error status codes with their response body schemas

### Requirement: Route handlers have no try/except
API route handlers SHALL NOT contain try/except blocks for `DomainError` or `ValueError`. Error translation is handled exclusively by the exception handler middleware.

#### Scenario: Route handler is a clean pass-through
- **WHEN** an API route handler calls an application service
- **THEN** it SHALL call the service directly without wrapping in try/except
- **THEN** any `DomainError` raised SHALL propagate to the exception handler

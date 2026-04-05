## MODIFIED Requirements

### Requirement: DomainError with ErrorCode enum
The system SHALL define a single `DomainError` exception class in `domain/error.py` with an `ErrorCode` enum. All domain and application layer errors that represent business rule violations or entity lookup failures SHALL raise `DomainError` with the appropriate code.

`DomainError.__init__` SHALL accept four parameters: `code: ErrorCode`, `error_code: str`, `message: str`, and `context: dict[str, Any] | None = None`.

Error codes:
- `NOT_FOUND` — entity does not exist
- `VALIDATION` — invalid input or business rule violation
- `CONFLICT` — scheduling conflict detected
- `NO_ROUTE` — no path exists between stops

#### Scenario: Domain model raises DomainError for validation failure
- **WHEN** a domain entity or value object receives invalid input
- **THEN** a `DomainError` with `ErrorCode.VALIDATION`, a specific `error_code`, and optional `context` SHALL be raised

#### Scenario: Application service raises DomainError for not found
- **WHEN** an application service cannot find a requested entity
- **THEN** a `DomainError` with `ErrorCode.NOT_FOUND`, a specific `error_code`, and `context` containing the entity ID SHALL be raised

#### Scenario: Domain service raises DomainError for no route
- **WHEN** the route finder cannot find a path between two stops
- **THEN** a `DomainError` with `ErrorCode.NO_ROUTE`, `error_code="NO_ROUTE_BETWEEN_STOPS"`, and `context={"from_stop_id": ..., "to_stop_id": ...}` SHALL be raised

### Requirement: ConflictError as DomainError subclass
`ConflictError` SHALL be a subclass of `DomainError` with `ErrorCode.CONFLICT` and SHALL carry the `ServiceConflicts` domain object as structured detail. It SHALL pass `error_code="SCHEDULING_CONFLICT"` to the parent constructor.

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

For non-conflict errors, the handler SHALL return `{"detail": {"error_code": "<error_code>", "message": "<message>", "context": {<context or empty>}}}`.

For ConflictError, the handler SHALL continue returning the existing structured conflict detail format.

#### Scenario: NOT_FOUND error returns 404 with structured detail
- **WHEN** a request triggers a `DomainError` with `ErrorCode.NOT_FOUND`
- **THEN** the API SHALL return HTTP 404 with `{"detail": {"error_code": "...", "message": "...", "context": {...}}}`

#### Scenario: VALIDATION error returns 400 with structured detail
- **WHEN** a request triggers a `DomainError` with `ErrorCode.VALIDATION`
- **THEN** the API SHALL return HTTP 400 with `{"detail": {"error_code": "...", "message": "...", "context": {...}}}`

#### Scenario: CONFLICT error returns 409 with existing structured detail
- **WHEN** a request triggers a `ConflictError`
- **THEN** the API SHALL return HTTP 409 with the existing structured conflict detail format

#### Scenario: NO_ROUTE error returns 422 with structured detail
- **WHEN** a request triggers a `DomainError` with `ErrorCode.NO_ROUTE`
- **THEN** the API SHALL return HTTP 422 with `{"detail": {"error_code": "...", "message": "...", "context": {...}}}`

### Requirement: Route handlers have no try/except
API route handlers SHALL NOT contain try/except blocks for `DomainError` or `ValueError`. Error translation is handled exclusively by the exception handler middleware.

#### Scenario: Route handler is a clean pass-through
- **WHEN** an API route handler calls an application service
- **THEN** it SHALL call the service directly without wrapping in try/except
- **THEN** any `DomainError` raised SHALL propagate to the exception handler

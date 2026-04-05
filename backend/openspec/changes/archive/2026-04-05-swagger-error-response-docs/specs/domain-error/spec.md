## MODIFIED Requirements

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

#### Scenario: Route handlers have no try/except
- **WHEN** an API route handler calls an application service
- **THEN** it SHALL call the service directly without wrapping in try/except
- **THEN** any `DomainError` raised SHALL propagate to the exception handler

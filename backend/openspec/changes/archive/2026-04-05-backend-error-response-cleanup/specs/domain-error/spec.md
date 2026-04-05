## MODIFIED Requirements

### Requirement: Unified FastAPI exception handler
The system SHALL register a single `DomainError` exception handler in FastAPI that maps error codes to HTTP status codes:

| ErrorCode    | HTTP Status |
|-------------|-------------|
| NOT_FOUND   | 404         |
| VALIDATION  | 400         |
| CONFLICT    | 409         |
| NO_ROUTE    | 422         |

The handler SHALL return a unified JSON response for ALL errors (including `ConflictError`) with `detail` containing only `error_code` and `context` — the `message` field SHALL NOT be included in the response body.

For `ConflictError`, the handler SHALL serialize the conflict lists (vehicle_conflicts, block_conflicts, interlocking_conflicts, battery_conflicts) into the `context` field.

The handler SHALL log the original `message` at WARNING level before returning the response, including `error_code` and `context` as structured log fields.

The error handler's response shapes SHALL be documented in OpenAPI via Pydantic response models declared on route decorators.

#### Scenario: VALIDATION error returns 400 without message
- **WHEN** a request triggers a `DomainError` with `ErrorCode.VALIDATION`, message `"Service name must not be empty"`, and no context
- **THEN** the API SHALL return HTTP 400 with `{"detail": {"error_code": "VALIDATION", "context": {}}}`
- **THEN** the response body SHALL NOT contain a `message` field in `detail`

#### Scenario: NOT_FOUND error returns 404 with context only
- **WHEN** a request triggers a `DomainError` with `ErrorCode.NOT_FOUND`, message `"Service 42 not found"`, and context `{"service_id": 42}`
- **THEN** the API SHALL return HTTP 404 with `{"detail": {"error_code": "NOT_FOUND", "context": {"service_id": 42}}}`
- **THEN** the response body SHALL NOT contain a `message` field in `detail`

#### Scenario: NO_ROUTE error returns 422 with context only
- **WHEN** a request triggers a `DomainError` with `ErrorCode.NO_ROUTE`, message `"No route between abc-1 and abc-2"`, and context `{"from_stop_id": "abc-1", "to_stop_id": "abc-2"}`
- **THEN** the API SHALL return HTTP 422 with `{"detail": {"error_code": "NO_ROUTE", "context": {"from_stop_id": "abc-1", "to_stop_id": "abc-2"}}}`

#### Scenario: CONFLICT error returns 409 with conflict data in context
- **WHEN** a request triggers a `ConflictError` with vehicle conflicts and block conflicts
- **THEN** the API SHALL return HTTP 409 with `{"detail": {"error_code": "SCHEDULING_CONFLICT", "context": {"vehicle_conflicts": [...], "block_conflicts": [...], "interlocking_conflicts": [...], "battery_conflicts": [...]}}}`
- **THEN** the response body SHALL NOT contain a `message` field in `detail`
- **THEN** the conflict lists within `context` SHALL use the same serialization format as before (vehicle_id, service_a_id, service_b_id, reason, etc.)

#### Scenario: Error message is logged server-side
- **WHEN** a request triggers a `DomainError` with message `"Service 42 not found"` and code `NOT_FOUND`
- **THEN** the error handler SHALL log at WARNING level with the message text and structured fields for error_code and context

#### Scenario: Error response shapes are visible in Swagger
- **WHEN** a developer opens Swagger UI
- **THEN** all routes that can produce `DomainError` SHALL show the applicable error status codes with their response body schemas

### Requirement: Route handlers have no try/except
API route handlers SHALL NOT contain try/except blocks for `DomainError` or `ValueError`. Error translation is handled exclusively by the exception handler middleware.

#### Scenario: Route handler is a clean pass-through
- **WHEN** an API route handler calls an application service
- **THEN** it SHALL call the service directly without wrapping in try/except
- **THEN** any `DomainError` raised SHALL propagate to the exception handler

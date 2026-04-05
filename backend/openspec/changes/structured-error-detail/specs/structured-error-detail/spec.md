## ADDED Requirements

### Requirement: DomainError carries error_code and context
`DomainError.__init__` SHALL accept `error_code: str` and `context: dict[str, Any] | None = None` parameters in addition to existing `code` and `message`. The `error_code` SHALL be a `SCREAMING_SNAKE_CASE` string. The `context` SHALL carry structured data about what caused the error.

#### Scenario: DomainError stores error_code and context
- **WHEN** a `DomainError` is raised with `error_code="STOP_NOT_FOUND"` and `context={"stop_id": "abc-123"}`
- **THEN** `exc.error_code` SHALL equal `"STOP_NOT_FOUND"` and `exc.context` SHALL equal `{"stop_id": "abc-123"}`

#### Scenario: DomainError with no context defaults to None
- **WHEN** a `DomainError` is raised with only `error_code="EMPTY_SERVICE_NAME"` and no context
- **THEN** `exc.context` SHALL be `None`

### Requirement: Non-conflict error handler returns structured detail
The domain error handler SHALL return `{"detail": {"error_code": "<code>", "message": "<msg>", "context": {<data>}}}` for all non-conflict `DomainError` instances. When `context` is None, the response SHALL include `"context": {}`.

#### Scenario: VALIDATION error with context returns structured detail
- **WHEN** a `DomainError` with `ErrorCode.VALIDATION`, `error_code="STOP_NOT_FOUND"`, and `context={"stop_id": "abc-123"}` is handled
- **THEN** the response SHALL be HTTP 400 with `{"detail": {"error_code": "STOP_NOT_FOUND", "message": "Stop abc-123 not found", "context": {"stop_id": "abc-123"}}}`

#### Scenario: NO_ROUTE error with context returns structured detail
- **WHEN** a `DomainError` with `ErrorCode.NO_ROUTE`, `error_code="NO_ROUTE_BETWEEN_STOPS"`, and `context={"from_stop_id": "abc", "to_stop_id": "def"}` is handled
- **THEN** the response SHALL be HTTP 422 with `{"detail": {"error_code": "NO_ROUTE_BETWEEN_STOPS", "message": "...", "context": {"from_stop_id": "abc", "to_stop_id": "def"}}}`

#### Scenario: VALIDATION error without context returns empty context
- **WHEN** a `DomainError` with `ErrorCode.VALIDATION`, `error_code="EMPTY_SERVICE_NAME"`, and no context is handled
- **THEN** the response SHALL be HTTP 400 with `{"detail": {"error_code": "EMPTY_SERVICE_NAME", "message": "Service name must not be empty", "context": {}}}`

#### Scenario: ConflictError response shape is unchanged
- **WHEN** a `ConflictError` is handled
- **THEN** the response SHALL remain HTTP 409 with the existing structured conflict detail format

### Requirement: Error codes with context
The following errors SHALL include structured context:

| error_code | context |
|---|---|
| `STOP_NOT_FOUND` | `{"stop_id": "<uuid>"}` |
| `NO_ROUTE_BETWEEN_STOPS` | `{"from_stop_id": "<uuid>", "to_stop_id": "<uuid>"}` |
| `SAME_ORIGIN_DESTINATION` | `{"stop_id": "<uuid>"}` |
| `VEHICLE_NOT_FOUND` | `{"vehicle_id": "<uuid>"}` |
| `SERVICE_NOT_FOUND` | `{"service_id": <int>}` |
| `BLOCK_NOT_FOUND` | `{"block_id": "<uuid>"}` |
| `UNKNOWN_NODE` | `{"node_id": "<uuid>"}` |
| `ENTRY_NODE_NOT_IN_ROUTE` | `{"node_id": "<uuid>"}` |
| `PLATFORM_NOT_FOUND` | `{"platform_id": "<uuid>"}` |
| `INSUFFICIENT_VEHICLES` | `{"needed": <int>, "available": <int>}` |

#### Scenario: Stop not found includes stop_id in context
- **WHEN** route builder cannot find stop with ID "abc-123"
- **THEN** the error context SHALL include `{"stop_id": "abc-123"}`

#### Scenario: No route includes both stop IDs in context
- **WHEN** route finder cannot find a path from "abc" to "def"
- **THEN** the error context SHALL include `{"from_stop_id": "abc", "to_stop_id": "def"}`

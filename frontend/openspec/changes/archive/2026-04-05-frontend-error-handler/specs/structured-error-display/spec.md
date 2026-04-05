## ADDED Requirements

### Requirement: ErrorDetail interface matches backend schema

The system SHALL define an `ErrorDetail` TypeScript interface in `shared/models/` with the fields:
- `error_code: string`
- `message: string`
- `context: Readonly<Record<string, unknown>>`

This interface SHALL be used to type the `detail` field of non-409 HTTP error responses.

#### Scenario: Backend returns structured error detail
- **WHEN** the backend returns a 400 response with `{ "detail": { "error_code": "STOP_NOT_FOUND", "message": "Stop not found", "context": { "stop_id": "uuid-123" } } }`
- **THEN** the `detail` field SHALL be parseable as `ErrorDetail`

### Requirement: UUID-to-name substitution in error messages

The `extractErrorMessage` function SHALL accept an optional `nameMap` parameter of type `ReadonlyMap<string, string>`. When provided, the function SHALL scan the `context` object's string values and replace any matching UUIDs found in the `message` text with their corresponding names from the map.

#### Scenario: Context UUID replaced with name
- **WHEN** the error has `message: "Stop abc-123 not found"` and `context: { "stop_id": "abc-123" }` and `nameMap` contains `"abc-123" → "P1A"`
- **THEN** the function SHALL return `"Stop P1A not found"`

#### Scenario: Context UUID not in name map
- **WHEN** the error has `message: "Stop abc-123 not found"` and `context: { "stop_id": "abc-123" }` and `nameMap` does not contain `"abc-123"`
- **THEN** the function SHALL return the original message `"Stop abc-123 not found"`

#### Scenario: No name map provided
- **WHEN** `extractErrorMessage` is called without a `nameMap` argument
- **THEN** the function SHALL return the message without any substitution (backward compatible)

#### Scenario: Multiple context values substituted
- **WHEN** the error has `message: "No route between abc-1 and abc-2"` and `context: { "from_stop_id": "abc-1", "to_stop_id": "abc-2" }` and `nameMap` contains both UUIDs
- **THEN** the function SHALL replace both UUIDs with their mapped names

### Requirement: Backward compatibility with string detail

The `extractErrorMessage` function SHALL continue to handle the legacy format where `detail` is a plain string. If `detail` is a string, it SHALL be returned as-is regardless of whether a `nameMap` is provided.

#### Scenario: Legacy string detail
- **WHEN** the error has `detail: "Something went wrong"`
- **THEN** the function SHALL return `"Something went wrong"`

### Requirement: Server error handling unchanged

The `extractErrorMessage` function SHALL continue to return a generic message for 5xx status codes, regardless of the response body structure.

#### Scenario: 500 error with structured body
- **WHEN** the error has status 500 and a structured `detail` body
- **THEN** the function SHALL return `"Something went wrong. Please try again later."`

### Requirement: Schedule editor builds name map from graph

When the `ScheduleEditorComponent` handles a non-409 error from route update, it SHALL build a name map from `service().graph` containing all nodes, edges, and vehicles, and pass it to `extractErrorMessage`.

#### Scenario: Route update returns 422 with stop UUID
- **WHEN** the route update returns 422 with `error_code: "NO_ROUTE_BETWEEN_STOPS"` and `context: { "from_stop_id": "uuid-p1a", "to_stop_id": "uuid-p3b" }` and the graph contains nodes with those IDs named "P1A" and "P3B"
- **THEN** the error message SHALL display with "P1A" and "P3B" instead of the raw UUIDs

### Requirement: Create service dialog builds name map from vehicles

When the `CreateServiceDialogComponent` handles a creation error, it SHALL build a name map from the loaded `vehicles()` list and pass it to `extractErrorMessage`.

#### Scenario: Service creation returns 400 with vehicle UUID
- **WHEN** service creation returns 400 with `error_code: "VEHICLE_NOT_FOUND"` and `context: { "vehicle_id": "uuid-v1" }` and vehicles list contains a vehicle with that ID named "V1"
- **THEN** the error message SHALL display with "V1" instead of the raw UUID

### Requirement: Block config builds name map from blocks

When the `BlockConfigComponent` handles a block update error, it SHALL build a name map from the loaded `blocks()` list and pass it to `extractErrorMessage`.

#### Scenario: Block update returns 404 with block UUID
- **WHEN** block update returns 404 with `error_code: "BLOCK_NOT_FOUND"` and `context: { "block_id": "uuid-b3" }` and blocks list contains a block with that ID named "B3"
- **THEN** the error message SHALL display with "B3" instead of the raw UUID

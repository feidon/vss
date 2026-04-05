## MODIFIED Requirements

### Requirement: ErrorDetail interface matches backend schema

The system SHALL define an `ErrorDetail` TypeScript interface in `shared/models/` with the fields:
- `error_code: string`
- `context: Readonly<Record<string, unknown>>`

This interface SHALL NOT include a `message` field, as the backend no longer sends one.

#### Scenario: Backend returns structured error detail
- **WHEN** the backend returns a 400 response with `{ "detail": { "error_code": "STOP_NOT_FOUND", "context": { "stop_id": "uuid-123" } } }`
- **THEN** the `detail` field SHALL be parseable as `ErrorDetail`

### Requirement: UUID-to-name substitution in error messages

The `extractErrorMessage` function SHALL accept an optional `nameMap` parameter of type `ReadonlyMap<string, string>`. When provided and a formatter exists for the `error_code`, the function SHALL pass the `context` and `nameMap` to the formatter to produce a user-facing message with resolved names.

#### Scenario: Context UUID replaced with name
- **WHEN** the error has `error_code: "STOP_NOT_FOUND"` and `context: { "stop_id": "abc-123" }` and `nameMap` contains `"abc-123" → "P1A"`
- **THEN** the function SHALL return `'Stop "P1A" not found'`

#### Scenario: Context UUID not in name map
- **WHEN** the error has `error_code: "NO_ROUTE_BETWEEN_STOPS"` and `context: { "from_stop_id": "uuid-1", "to_stop_id": "uuid-2" }` and `nameMap` does not contain either UUID
- **THEN** the formatter SHALL return `null` and the function SHALL return the caller-provided `fallback` string

#### Scenario: No name map provided
- **WHEN** `extractErrorMessage` is called without a `nameMap` argument
- **THEN** the function SHALL use an empty map, and formatters that require name resolution SHALL return `null`, causing the function to return the `fallback` string

#### Scenario: Multiple context values substituted
- **WHEN** the error has `error_code: "NO_ROUTE_BETWEEN_STOPS"` and `context: { "from_stop_id": "abc-1", "to_stop_id": "abc-2" }` and `nameMap` contains both UUIDs
- **THEN** the function SHALL return the formatter's result with both UUIDs replaced by their mapped names

### Requirement: Fallback behavior for unknown or unformattable errors

When the `error_code` has no registered formatter, or the formatter returns `null`, the function SHALL return the caller-provided `fallback` string. The function SHALL NOT attempt to read a `message` field from the response.

#### Scenario: Unknown error code returns fallback
- **WHEN** the error has `error_code: "SOME_FUTURE_ERROR"` and `context: {}`
- **THEN** the function SHALL return the caller-provided `fallback` string

#### Scenario: Formatter returns null returns fallback
- **WHEN** the error has `error_code: "VEHICLE_NOT_FOUND"` and `context: { "vehicle_id": "v1-uuid" }` but `nameMap` does not contain `"v1-uuid"`
- **THEN** the function SHALL return the caller-provided `fallback` string

## REMOVED Requirements

### Requirement: Backward compatibility with string detail — message fallback path
**Reason**: The backend no longer sends a `message` field in error responses. The `detail.message` fallback in `extractErrorMessage` is dead code.
**Migration**: Callers already provide a `fallback` parameter which serves the same purpose. No caller changes needed.

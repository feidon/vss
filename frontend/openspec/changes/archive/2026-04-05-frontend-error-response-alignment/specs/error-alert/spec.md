## MODIFIED Requirements

### Requirement: Extract error message from HTTP responses
The system SHALL provide an `extractErrorMessage` utility function that extracts a user-facing message from an `HttpErrorResponse`. The function SHALL accept the error, a fallback string, and an optional `nameMap`.

#### Scenario: Server error returns constant message
- **WHEN** the HTTP response has status >= 500
- **THEN** the function SHALL return "Something went wrong. Please try again later." regardless of the response body

#### Scenario: 422 with string detail
- **WHEN** the HTTP response has status 422 and `error.detail` is a string (e.g., "Start time must be in the future")
- **THEN** the function SHALL return that string as the error message

#### Scenario: 4xx with structured error_code detail
- **WHEN** the HTTP response has status 4xx and `error.detail` is an object with an `error_code` string field
- **THEN** the function SHALL look up a formatter for that code, pass `context` and `nameMap`, and return the formatted message if non-null, otherwise return the `fallback` string

#### Scenario: Unrecognized error format
- **WHEN** the HTTP response has no parseable `detail` field and status < 500
- **THEN** the function SHALL return the provided fallback string

## REMOVED Requirements

### Requirement: Extract error message from HTTP responses — detail.message object fallback
**Reason**: The backend no longer sends `message` in error detail objects. The scenario "4xx with object detail containing message" is no longer reachable.
**Migration**: The `fallback` parameter serves this purpose. No caller changes needed.

## Why

VALIDATION and NO_ROUTE errors return `{"detail": "<message>"}` — a bare string. The frontend cannot determine *which* stop failed or *which* pair of stops had no route without parsing the message. ConflictError already returns structured detail with specific IDs; other error types should follow the same pattern so the frontend can highlight the problematic input.

## What Changes

- Add `error_code: str` and `context: dict` to `DomainError` so each raise site can attach structured context (e.g., `{"stop_id": "..."}`, `{"from_stop_id": "...", "to_stop_id": "..."}`)
- Update the error handler to return `{"detail": {"error_code": "...", "message": "...", "context": {...}}}` for all non-conflict errors
- Update `ErrorResponse` Pydantic model to match the new shape
- Add contextual data to raise sites where the frontend can act on it (stop not found, no route, vehicle not found, etc.)

## Non-goals

- Collecting multiple validation errors per request
- Changing ConflictError response shape
- Changing HTTP status codes
- Adding context to internal invariant errors (entries ordering, connectivity checks) — those stay with empty context

## Capabilities

### New Capabilities
- `structured-error-detail`: Defines the `error_code` + `context` fields on DomainError and the structured response shape

### Modified Capabilities
- `domain-error`: DomainError gains `error_code` and `context` fields; raise sites supply them
- `swagger-error-schemas`: ErrorResponse model changes from `detail: str` to structured object

## Impact

- **domain/error.py**: DomainError constructor gains `error_code` and `context` params
- **All DomainError raise sites** (~25): add `error_code` and optional `context`
- **api/error_handler.py**: Build structured detail dict for non-conflict errors
- **api/shared/schemas.py**: Update `ErrorResponse` model
- **Tests**: Update error handler tests, assertions on response shape
- **Frontend**: Can switch on `error_code` and use `context` to highlight specific inputs
- **BREAKING**: Response body shape changes for 400/404/422 errors

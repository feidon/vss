### Requirement: Error response Pydantic models
The system SHALL define Pydantic response models in `api/shared/schemas.py` for all error response shapes returned by the domain error handler.

- `ErrorDetail`: SHALL have two fields:
  - `error_code: str` — the error code enum value
  - `context: dict[str, Any]` — additional context for the error (defaults to empty dict)
  - The model SHALL NOT have a `message` field.
- `ErrorResponse`: SHALL have a single field `detail: ErrorDetail`.

#### Scenario: ErrorDetail model matches standard error handler output
- **WHEN** the domain error handler returns `{"detail": {"error_code": "STOP_NOT_FOUND", "context": {"stop_id": "uuid-123"}}}`
- **THEN** the `ErrorDetail` model SHALL validate that output successfully

#### Scenario: ErrorDetail model matches conflict error handler output
- **WHEN** the domain error handler returns `{"detail": {"error_code": "SCHEDULING_CONFLICT", "context": {"vehicle_conflicts": [...], "block_conflicts": [...]}}}`
- **THEN** the `ErrorDetail` model SHALL validate that output successfully

### Requirement: Reusable error response constants
The system SHALL define response dict constants in `api/shared/schemas.py` for each error category:

| Constant | Status | Model | Description |
|----------|--------|-------|-------------|
| `NOT_FOUND_RESPONSE` | 404 | `ErrorResponse` | Resource not found |
| `VALIDATION_RESPONSE` | 400 | `ErrorResponse` | Validation error |
| `CONFLICT_RESPONSE` | 409 | `ErrorResponse` | Scheduling conflicts detected |
| `NO_ROUTE_RESPONSE` | 422 | `ErrorResponse` | No route between stops |

All constants SHALL use `ErrorResponse` as the model — there is no separate `ConflictDetailResponse`.

#### Scenario: Constants are usable in route decorators
- **WHEN** a route decorator uses `responses={**NOT_FOUND_RESPONSE, **CONFLICT_RESPONSE}`
- **THEN** Swagger SHALL display 404 and 409 as documented response statuses with `ErrorResponse` as the body schema

### Requirement: All routes declare error responses
Every API route that can produce a `DomainError` SHALL declare the applicable error responses via the `responses` parameter on its route decorator.

The mapping SHALL be:

| Route | Error Responses |
|-------|----------------|
| `PATCH /api/blocks/{id}` | 404 |
| `POST /api/services` | 400 |
| `GET /api/services/{id}` | 404 |
| `PATCH /api/services/{id}/route` | 404, 400, 409, 422 |
| `DELETE /api/services/{id}` | 404 |

Routes that only return success (e.g., `GET /api/blocks`, `GET /api/services`, `GET /api/vehicles`) SHALL NOT declare error responses beyond FastAPI defaults.

#### Scenario: Swagger shows unified ErrorDetail schema for all errors
- **WHEN** a developer opens Swagger UI for any error-producing route
- **THEN** all error status codes (400, 404, 409, 422) SHALL use the same `ErrorDetail` schema with `error_code` and `context` fields only

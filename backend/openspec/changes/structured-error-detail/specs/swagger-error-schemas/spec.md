## MODIFIED Requirements

### Requirement: Error response Pydantic models
The system SHALL define Pydantic response models in `api/shared/schemas.py` for all error response shapes returned by the domain error handler.

- `ErrorDetail`: SHALL have fields `error_code: str`, `message: str`, and `context: dict[str, Any]`.
- `ErrorResponse`: SHALL have a single field `detail: ErrorDetail`.
- `ConflictDetailResponse`: SHALL remain unchanged with field `detail: ConflictDetail`.

#### Scenario: ErrorResponse model matches structured error handler output
- **WHEN** the domain error handler returns `{"detail": {"error_code": "SERVICE_NOT_FOUND", "message": "Service 1 not found", "context": {"service_id": 1}}}`
- **THEN** the `ErrorResponse` model SHALL validate that output successfully

#### Scenario: ConflictDetailResponse model matches conflict error handler output
- **WHEN** the domain error handler returns a 409 response with structured conflict detail
- **THEN** the `ConflictDetailResponse` model SHALL validate that output successfully

### Requirement: Reusable error response constants
The system SHALL define response dict constants in `api/shared/schemas.py` for each error category:

| Constant | Status | Model | Description |
|----------|--------|-------|-------------|
| `NOT_FOUND_RESPONSE` | 404 | `ErrorResponse` | Resource not found |
| `VALIDATION_RESPONSE` | 400 | `ErrorResponse` | Validation error |
| `CONFLICT_RESPONSE` | 409 | `ConflictDetailResponse` | Scheduling conflicts detected |
| `NO_ROUTE_RESPONSE` | 422 | `ErrorResponse` | No route between stops |

#### Scenario: Constants are usable in route decorators
- **WHEN** a route decorator uses `responses={**NOT_FOUND_RESPONSE, **CONFLICT_RESPONSE}`
- **THEN** Swagger SHALL display 404 and 409 as documented response statuses with their respective body schemas

### Requirement: All routes declare error responses
Every API route that can produce a `DomainError` SHALL declare the applicable error responses via the `responses` parameter on its route decorator.

| Route | Error Responses |
|-------|----------------|
| `PATCH /api/blocks/{id}` | 404 |
| `POST /api/services` | 400 |
| `GET /api/services/{id}` | 404 |
| `PATCH /api/services/{id}/route` | 404, 400, 409, 422 |
| `DELETE /api/services/{id}` | 404 |
| `POST /api/schedules/generate` | 400 |

#### Scenario: Swagger shows error responses for PATCH /api/services/{id}/route
- **WHEN** a developer opens Swagger UI for `PATCH /api/services/{id}/route`
- **THEN** the documented responses SHALL include 200, 400, 404, 409, and 422

#### Scenario: POST /api/schedules/generate shows 400 in Swagger
- **WHEN** a developer opens Swagger UI for `POST /api/schedules/generate`
- **THEN** the documented responses SHALL include 400

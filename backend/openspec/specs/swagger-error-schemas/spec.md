### Requirement: Error response Pydantic models
The system SHALL define Pydantic response models in `api/shared/schemas.py` for all error response shapes returned by the domain error handler.

- `ErrorResponse`: SHALL have a single field `detail: str` representing the error message.
- `ConflictDetailResponse`: SHALL have a single field `detail: ConflictDetail` where `ConflictDetail` is a model with:
  - `message: str`
  - `vehicle_conflicts: list[VehicleConflictSchema]`
  - `block_conflicts: list[BlockConflictSchema]`
  - `interlocking_conflicts: list[InterlockingConflictSchema]`
  - `battery_conflicts: list[BatteryConflictSchema]`

Each nested conflict schema SHALL mirror the dict structure produced by `error_handler._build_conflict_detail()`.

#### Scenario: ErrorResponse model matches simple error handler output
- **WHEN** the domain error handler returns `{"detail": "Service 1 not found"}`
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

Each constant SHALL be a dict in the format `{status_code: {"model": Model, "description": "..."}}` suitable for merging into FastAPI's `responses` parameter.

#### Scenario: Constants are usable in route decorators
- **WHEN** a route decorator uses `responses={**NOT_FOUND_RESPONSE, **CONFLICT_RESPONSE}`
- **THEN** Swagger SHALL display 404 and 409 as documented response statuses with their respective body schemas

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
| `POST /api/routes/validate` | 400, 422 |

Routes that only return success (e.g., `GET /api/blocks`, `GET /api/services`, `GET /api/vehicles`) SHALL NOT declare error responses beyond FastAPI defaults.

#### Scenario: Swagger shows error responses for PATCH /api/services/{id}/route
- **WHEN** a developer opens Swagger UI for `PATCH /api/services/{id}/route`
- **THEN** the documented responses SHALL include 200, 400, 404, 409, and 422 with their body schemas

#### Scenario: Swagger shows no extra error responses for GET /api/blocks
- **WHEN** a developer opens Swagger UI for `GET /api/blocks`
- **THEN** the documented responses SHALL only include 200 (and FastAPI's auto 422)

#### Scenario: New route without responses declaration is visibly missing error docs
- **WHEN** a developer adds a new route that raises `DomainError`
- **THEN** the absence of `responses` parameter SHALL be visible by comparison with existing routes that all declare their error responses

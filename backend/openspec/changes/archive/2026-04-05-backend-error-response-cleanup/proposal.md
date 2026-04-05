## Why

The backend error handler currently sends the `message` field in error responses (e.g., `"Service 123 not found"`, `"Entry references node abc-def not in route"`). These messages contain internal IDs that mean nothing to users. The frontend already has `extractErrorMessage` which consumes the `message` directly — but a cleaner approach is for the frontend to own its user-facing copy based on `error_code` and `context`, while the backend keeps `message` only in logs for debugging.

## What Changes

- **Unify all error responses into one shape** — every `DomainError` (including `ConflictError`) returns `{"detail": {"error_code": "...", "context": {...}}}`. Conflict data (vehicle_conflicts, block_conflicts, etc.) moves into `context`.
- **Remove `message` from all error responses** — the handler will return only `error_code` and `context` in `detail`
- **Log the error message server-side** — add structured logging in the error handler so `message` (with IDs) is preserved for debugging
- **Update Pydantic schemas** — single `ErrorDetail` model for all errors; remove `ConflictDetail`, `ConflictDetailResponse`, and nested conflict schemas
- **Update error handler tests** — verify the unified response shape and logging behavior
- **BREAKING**: The `message` field is removed from all error responses. The 409 conflict response shape changes — conflict lists move into `context`. Frontend must derive display text from `error_code` and read conflict data from `context`.

## Non-goals

- Changing how/where `DomainError` is raised in domain or application layers — the `message` field stays on the exception for logging
- Frontend changes — those belong in the frontend repo as a companion change

## Capabilities

### New Capabilities

_None — this modifies existing error handling behavior._

### Modified Capabilities

- `domain-error`: The error handler uses a unified response shape for all errors — `message` is removed, conflict data moves into `context`, only `error_code` and `context` are sent
- `swagger-error-schemas`: Single `ErrorDetail` model for all errors; `ConflictDetail`, `ConflictDetailResponse`, and nested conflict schemas are removed

## Impact

- **`api/error_handler.py`**: Unified response construction for all errors; remove `_build_conflict_detail`; add logging
- **`api/shared/schemas.py`**: Single `ErrorDetail` model; remove `ConflictDetail`, `ConflictDetailResponse`, `VehicleConflictSchema`, `BlockConflictSchema`, `InterlockingConflictSchema`, `ConflictBatterySchema`; `CONFLICT_RESPONSE` uses `ErrorResponse`
- **`tests/`**: All error handler tests need updating for unified response shape
- **Frontend (companion change)**: `extractErrorMessage` must switch to error-code-based message rendering. `ConflictAlertComponent` must read conflict lists from `detail.context` instead of `detail` directly.

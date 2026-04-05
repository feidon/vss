## Context

The backend error handler currently has two response shapes:
1. **Standard errors** (400/404/422): `{ "error_code": "...", "message": "...", "context": {...} }`
2. **Conflict errors** (409): `{ "message": "...", "vehicle_conflicts": [...], "block_conflicts": [...], ... }`

The `message` field in standard errors contains developer-oriented text with internal IDs (e.g., `"Service 123 not found"`). The conflict response has a completely different structure with its own Pydantic models (`ConflictDetail`, `VehicleConflictSchema`, etc.).

The frontend already has `error_code` and `context` available. It should own the user-facing error text. And the conflict data is just structured context — no reason for it to have a separate response envelope.

## Goals / Non-Goals

**Goals:**
- Unify all error responses into one shape: `{ "error_code": "...", "context": {...} }` — no `message`
- Move conflict lists (vehicle_conflicts, block_conflicts, etc.) into `context`
- Log the original `message` server-side for debugging
- Simplify Pydantic schemas — one `ErrorDetail` model for all errors
- Remove `ConflictDetail`, `ConflictDetailResponse`, and nested conflict schemas

**Non-Goals:**
- Changing how `DomainError` or `ConflictError` is raised (the exception classes stay the same)
- Frontend changes (separate companion change)
- Adding a logging framework — use Python's stdlib `logging`

## Decisions

### 1. Unified response shape for all errors

**Choice:** Every `DomainError` (including `ConflictError`) returns:
```json
{ "detail": { "error_code": "SCHEDULING_CONFLICT", "context": { "vehicle_conflicts": [...], ... } } }
```

**Rationale:** One response shape means one Pydantic model, one error handler path, and one frontend parsing strategy. The conflict data is just richer context — it doesn't need its own envelope. The frontend already branches on `error.status === 409` to decide which component to show, so it can read the conflict lists from `context` just as easily.

**Alternative considered:** Keep separate shapes but remove `message` from both. Rejected — maintaining two shapes for no benefit adds complexity to both backend schemas and frontend parsing.

### 2. Remove `message` from all responses, log it server-side

**Choice:** The error handler returns only `error_code` and `context`. It logs at WARNING level with the original `message`, error code, and context.

**Rationale:** The `message` is only useful for backend debugging. For standard errors it contains IDs; for conflicts it's a fixed string ("Service has scheduling conflicts") that the frontend hardcodes anyway.

### 3. Remove conflict-specific Pydantic schemas

**Choice:** Delete `ConflictDetail`, `ConflictDetailResponse`, `VehicleConflictSchema`, `BlockConflictSchema`, `InterlockingConflictSchema`, `ConflictBatterySchema`. The `CONFLICT_RESPONSE` constant uses `ErrorResponse` like all other error responses.

**Rationale:** With the unified shape, these models are unnecessary. The `context` field is `dict[str, Any]` — the conflict structure is implicit. The frontend has its own typed interfaces (`ConflictResponse`, `VehicleConflict`, etc.) for the data within `context`.

### 4. Build conflict context via `_build_conflict_context`

**Choice:** Rename `_build_conflict_detail` to `_build_conflict_context` and have it return just the dict of conflict lists (without `message`). The error handler puts this into the `context` field.

**Rationale:** Keeps the serialization logic for conflict domain objects in one place, but it now returns context data rather than a full response detail.

## Risks / Trade-offs

- **[Breaking API change for 409 responses]** → Frontend `ConflictAlertComponent` reads from `detail.context` instead of `detail`. The schedule editor's `if (err.status === 409)` check still works; it just reads `detail.context.vehicle_conflicts` instead of `detail.vehicle_conflicts`. Small change, same deploy window.
- **[Lost type safety in Swagger for conflict response]** → The conflict structure inside `context` is `dict[str, Any]` in Swagger, not the previously typed schema. Acceptable trade-off — the frontend has its own TypeScript interfaces, and the backend contract is `error_code` + `context`.
- **[Breaking API change for all error responses]** → Frontend must be updated simultaneously. Since this is a monorepo with local dev, both changes can be made together.
- **[Frontend must maintain error code → message map]** → Small ongoing cost, but gives the frontend full control over user-facing copy.

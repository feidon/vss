## Context

Error responses are handled by a global `domain_error_handler` in `api/error_handler.py` that catches `DomainError` and maps `ErrorCode` to HTTP statuses. This works at runtime but is invisible to FastAPI's OpenAPI generation — Swagger shows only success responses and the auto-generated 422 for Pydantic validation.

The current approach creates a discoverability problem: developers adding new routes have no mechanism reminding them to declare error responses. The error handler silently catches everything, so routes "work" without any `responses` declaration.

## Goals / Non-Goals

**Goals:**
- All error statuses (400, 404, 409, 422/NO_ROUTE) appear in Swagger with correct body schemas
- A declarative helper makes it easy to attach the right error responses per route
- Future routes naturally get error docs without developers needing to remember the pattern

**Non-Goals:**
- Changing the error handler logic or status code mappings
- Changing the response body format
- Documenting FastAPI's built-in 422 (Pydantic validation) — already auto-generated

## Decisions

### 1. Error response Pydantic models in `api/shared/schemas.py`

Define `ErrorResponse` (simple string detail) and `ConflictDetailResponse` (structured 409 body) alongside existing shared schemas. These are pure documentation models — the error handler still builds dicts manually.

**Why here:** `api/shared/` already holds cross-cutting Pydantic schemas. Error responses are shared across all route modules.

**Alternative considered:** A separate `api/error_schemas.py` file. Rejected — there are only 2 models, not enough to justify a new file, and `shared/schemas.py` is the natural home.

### 2. Pre-built response dicts as constants

Define constants like `NOT_FOUND_RESPONSE`, `VALIDATION_RESPONSE`, `CONFLICT_RESPONSE`, `NO_ROUTE_RESPONSE` that each route can merge into its `responses` parameter:

```python
NOT_FOUND_RESPONSE = {404: {"model": ErrorResponse, "description": "Resource not found"}}
CONFLICT_RESPONSE = {409: {"model": ConflictDetailResponse, "description": "Scheduling conflicts detected"}}
```

Routes compose them: `responses={**NOT_FOUND_RESPONSE, **CONFLICT_RESPONSE}`.

**Why constants over a decorator:** Constants are explicit, greppable, and require no magic. A developer reads the route decorator and sees exactly which errors are documented. A custom decorator would hide the mapping and add abstraction for no gain.

**Alternative considered:** A `@error_responses(ErrorCode.NOT_FOUND, ErrorCode.CONFLICT)` decorator that auto-generates the `responses` dict from error codes. Rejected — it couples the OpenAPI declaration to the error code enum, making it harder to add per-route descriptions or override schemas. The constant approach is simpler and more explicit.

### 3. Per-route `responses` — manual but auditable

Each route explicitly declares its `responses` dict. This is intentional: it forces the developer to think about which errors an endpoint can produce.

**Discoverability aid:** The constants are defined right next to the error response models in `api/shared/schemas.py`. When a developer imports `ErrorResponse`, they see the response constants too. Combined with the existing `domain-error` spec and the pattern being visible in every route file, this creates enough friction to prevent undocumented errors.

### 4. Conflict detail model mirrors `_build_conflict_detail`

The `ConflictDetailResponse` schema mirrors the dict structure built by `error_handler._build_conflict_detail()`. This is documentation-only — the handler still returns a raw dict. If the handler's shape changes, the schema must be updated manually.

**Risk:** Schema drift if someone changes the handler but not the model. Mitigated by: the schema is in `api/shared/schemas.py` which is imported by all route modules, making it visible.

## Risks / Trade-offs

- **Manual sync between handler and schema** → The Pydantic models don't enforce the handler's output shape at runtime. A test should verify that the handler's output matches the schema.
- **NO_ROUTE (422) collides with FastAPI's auto 422** → Two different body shapes share HTTP 422. This pre-exists and is not changed here. The `responses` declaration will add the `ErrorResponse` model for 422, which may display alongside FastAPI's auto-generated validation error schema. Consider changing NO_ROUTE to 400 in a future change.

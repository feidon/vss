## Context

Currently non-conflict errors return `{"detail": "<message>"}`. ConflictError returns structured detail with block IDs, service IDs, etc. The frontend needs the same structured context for VALIDATION and NO_ROUTE errors to highlight which input caused the failure.

## Goals / Non-Goals

**Goals:**
- Every non-conflict error response includes `error_code`, `message`, and `context` dict
- Context carries relevant IDs (stop_id, vehicle_id, etc.) so the frontend can act on them
- Consistent response envelope across all non-conflict error types

**Non-Goals:**
- Multiple validation errors per request
- Changing ConflictError shape or HTTP status codes
- Adding context to internal invariant errors (those get empty context)

## Decisions

### 1. DomainError gains `error_code: str` and `context: dict`

**Constructor:** `DomainError(code, error_code, message, context=None)`
- `code: ErrorCode` — category for HTTP status mapping (existing)
- `error_code: str` — SCREAMING_SNAKE_CASE identifier (new)
- `message: str` — human-readable description (existing)
- `context: dict[str, Any] | None` — structured data about where the error occurred (new, optional, defaults to empty dict in response)

**Alternative considered:** Separate exception subclasses per error type (like ConflictError). Rejected — too many classes for ~25 error cases. A generic context dict keeps it simple.

### 2. Response shape for non-conflict errors

```json
{"detail": {"error_code": "STOP_NOT_FOUND", "message": "Stop abc-123 not found", "context": {"stop_id": "abc-123"}}}
```

When `context` is None/empty, it serializes as `{}`.

### 3. Context per error code

| error_code | context |
|---|---|
| `STOP_NOT_FOUND` | `{"stop_id": "<uuid>"}` |
| `NO_ROUTE_BETWEEN_STOPS` | `{"from_stop_id": "<uuid>", "to_stop_id": "<uuid>"}` |
| `SAME_ORIGIN_DESTINATION` | `{"stop_id": "<uuid>"}` |
| `VEHICLE_NOT_FOUND` | `{"vehicle_id": "<uuid>"}` |
| `SERVICE_NOT_FOUND` | `{"service_id": <int>}` |
| `BLOCK_NOT_FOUND` | `{"block_id": "<uuid>"}` |
| `UNKNOWN_NODE` | `{"node_id": "<uuid>"}` |
| `ENTRY_NODE_NOT_IN_ROUTE` | `{"node_id": "<uuid>"}` |
| `PLATFORM_NOT_FOUND` | `{"platform_id": "<uuid>"}` |
| `INSUFFICIENT_VEHICLES` | `{"needed": <int>, "available": <int>}` |
| All other codes | `{}` (no actionable context) |

### 4. ErrorResponse Pydantic model

Replace `ErrorResponse(detail: str)` with:
```python
class ErrorDetail(BaseModel):
    error_code: str
    message: str
    context: dict[str, Any]

class ErrorResponse(BaseModel):
    detail: ErrorDetail
```

### 5. ConflictError unchanged

ConflictError continues to pass through `_build_conflict_detail()` which returns its own structured shape. The `error_code`/`context` fields on the parent DomainError are set (`SCHEDULING_CONFLICT`, empty context) but not used in the response — the conflict detail format is already richer.

## Risks / Trade-offs

- **[Breaking API change]** → Frontend must read `detail.error_code`, `detail.message`, `detail.context` instead of `detail` as string. Co-deploy with frontend.
- **[Test churn]** → Tests asserting `{"detail": "..."}` must update to structured shape. Mechanical change.
- **[Context is untyped]** → `context: dict` has no schema enforcement per error_code. Acceptable tradeoff — each error_code's context is documented in the design table above.

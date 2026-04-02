## Context

Error handling is scattered across 3 route files (`api/service/routes.py`, `api/block/routes.py`, `api/route/routes.py`). Each route catches `ValueError`, inspects the message string to determine the HTTP status code, and raises `HTTPException`. One custom exception (`ConflictError` in `application/service/errors.py`) exists but follows a different pattern. This leads to fragile string matching like `"not found" in str(e)` and `str(e).startswith(f"Service {service_id}")`.

## Goals / Non-Goals

**Goals:**
- One `DomainError` with an `ErrorCode` enum that maps to HTTP status codes
- One FastAPI exception handler that translates `DomainError` → JSON response
- Clean route handlers with no try/except blocks

**Non-Goals:**
- Changing the conflict detail response shape (the structured conflict payload stays as-is)
- Adding i18n or user-facing error codes to the API contract
- Catching infrastructure errors (DB failures stay as 500)

## Decisions

### 1. Single `DomainError` class with `ErrorCode` enum

Place in `domain/error.py`:

```python
from enum import Enum

class ErrorCode(Enum):
    NOT_FOUND = "NOT_FOUND"
    VALIDATION = "VALIDATION"
    CONFLICT = "CONFLICT"
    NO_ROUTE = "NO_ROUTE"

class DomainError(Exception):
    def __init__(self, code: ErrorCode, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)
```

**Why `domain/error.py`**: The error is raised from domain models, domain services, and application services. Placing it in the domain layer lets all layers use it without violating the dependency rule (`api → application → domain ← infra`).

**Why single class + enum, not a class hierarchy**: The user's preference. A hierarchy (`NotFoundError`, `ValidationError`, etc.) adds classes without value when the only variation is the status code mapping. The enum makes the mapping explicit and the code grep-friendly.

**Alternative considered**: Keep `ConflictError` as a separate subclass because it carries structured data (`ServiceConflicts`). Decision: make `ConflictError` a subclass of `DomainError` that adds the `conflicts` field. This preserves the structured conflict detail while unifying the handler.

```python
# application/service/errors.py
from domain.error import DomainError, ErrorCode
from domain.domain_service.conflict import ServiceConflicts

class ConflictError(DomainError):
    def __init__(self, conflicts: ServiceConflicts) -> None:
        self.conflicts = conflicts
        super().__init__(ErrorCode.CONFLICT, "Service has scheduling conflicts")
```

### 2. ErrorCode → HTTP status mapping in the handler

Place in `api/error_handler.py`:

```python
from fastapi import Request
from fastapi.responses import JSONResponse
from domain.error import DomainError, ErrorCode

STATUS_MAP = {
    ErrorCode.NOT_FOUND: 404,
    ErrorCode.VALIDATION: 400,
    ErrorCode.CONFLICT: 409,
    ErrorCode.NO_ROUTE: 422,
}

async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
    status = STATUS_MAP.get(exc.code, 400)
    # Special case: ConflictError has structured detail
    if exc.code == ErrorCode.CONFLICT and hasattr(exc, "conflicts"):
        detail = _build_conflict_detail(exc)
    else:
        detail = exc.message
    return JSONResponse(status_code=status, content={"detail": detail})
```

**Why `api/error_handler.py`**: HTTP status codes are an API concern. The domain defines error codes; the API layer decides how to present them.

**Alternative considered**: Putting the status map in the enum itself (`ErrorCode.NOT_FOUND.status = 404`). Rejected because HTTP status is not a domain concept.

### 3. Register handler in `main.py`

```python
from api.error_handler import domain_error_handler
from domain.error import DomainError

app.add_exception_handler(DomainError, domain_error_handler)
```

### 4. Refactor raise sites

All `ValueError` raises in domain and application layers become `DomainError`:

| Current | New |
|---------|-----|
| `raise ValueError("Block ... not found")` | `raise DomainError(ErrorCode.NOT_FOUND, "Block ... not found")` |
| `raise ValueError("Service name cannot be empty")` | `raise DomainError(ErrorCode.VALIDATION, "Service name cannot be empty")` |
| `raise ValueError("No route between ...")` | `raise DomainError(ErrorCode.NO_ROUTE, "No route between ...")` |
| `raise ConflictError(conflicts)` | _(unchanged — already a DomainError subclass)_ |

Route handlers drop all try/except blocks and just call the service.

## Risks / Trade-offs

- **[Risk] Missed raise site** → Mitigation: grep for `raise ValueError` across domain/ and application/ before marking complete. Any remaining `ValueError` would surface as 500 in tests.
- **[Risk] Test assertions break** → Mitigation: tests that assert `ValueError` need updating to assert `DomainError`. Do this per-module in the task list.
- **[Trade-off] `ConflictError` subclass vs. flat `DomainError`**: Subclass adds one class but keeps the conflict detail handler clean. Worth it — the alternative is stuffing `ServiceConflicts` into a generic `detail` field.

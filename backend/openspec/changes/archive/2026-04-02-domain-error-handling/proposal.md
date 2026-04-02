## Why

Every API route manually catches `ValueError` and `ConflictError`, then infers the HTTP status code by string-matching on the error message (e.g., `"not found" in str(e)` → 404). This is fragile — a typo in a domain error message silently changes the HTTP response — and duplicates the same try/except pattern across all route files.

## What Changes

- Introduce a single `DomainError` base exception with an `ErrorCode` enum that explicitly declares the error category (NOT_FOUND, VALIDATION, CONFLICT, etc.)
- Replace all `ValueError` raises in domain and application layers with `DomainError(ErrorCode.XXX, message)`
- Register one FastAPI exception handler that maps `ErrorCode` → HTTP status code
- Remove all try/except blocks from API route handlers — routes become clean pass-throughs

## Non-goals

- Changing the shape of existing error response payloads (conflict details stay as-is)
- Adding error codes to the frontend contract (just internal cleanup)
- Structured error response envelope (keep it simple — `detail` field is sufficient)

## Capabilities

### New Capabilities
- `domain-error`: Unified `DomainError` exception with `ErrorCode` enum and FastAPI exception handler middleware

### Modified Capabilities

_(none — no existing spec-level requirements change)_

## Impact

- **domain/**: New `DomainError` + `ErrorCode` in a shared errors module; all `ValueError` raises replaced
- **application/**: `ConflictError` becomes a `DomainError` subclass or is replaced; service raises updated
- **api/**: Try/except blocks removed from all route handlers; one handler registered in `main.py`
- **tests/**: Error assertions updated to expect `DomainError` instead of `ValueError`

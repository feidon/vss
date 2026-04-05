## 1. Update Pydantic schemas

- [x] 1.1 Update `ErrorDetail` in `api/shared/schemas.py`: remove `message` field, keep `error_code: str` and `context: dict[str, Any]`
- [x] 1.2 Remove `ConflictDetail`, `ConflictDetailResponse`, `VehicleConflictSchema`, `BlockConflictSchema`, `InterlockingConflictSchema`, `ConflictBatterySchema`
- [x] 1.3 Update `CONFLICT_RESPONSE` constant to use `ErrorResponse` instead of `ConflictDetailResponse`

## 2. Update error handler

- [x] 2.1 Add `import logging` and create module logger in `api/error_handler.py`
- [x] 2.2 Unify response construction: all errors (including `ConflictError`) return `{"detail": {"error_code": "...", "context": {...}}}`
- [x] 2.3 Rename `_build_conflict_detail` to `_build_conflict_context` — return only the conflict lists dict (no `message`), used as the `context` value
- [x] 2.4 Add `logger.warning(...)` call with the original `message`, `error_code`, and `context` before returning the response

## 3. Update tests

- [x] 3.1 Update error handler tests to assert the unified response shape for all error types (no `message` in detail)
- [x] 3.2 Update 409 conflict tests to assert conflict data is nested under `detail.context`
- [x] 3.3 Update any API integration tests that assert on the old response shapes

## 4. Verify

- [x] 4.1 Run full test suite (`uv run pytest -m ''`) and confirm all pass
- [x] 4.2 Run linter (`uv run ruff check . && uv run lint-imports`) and confirm clean

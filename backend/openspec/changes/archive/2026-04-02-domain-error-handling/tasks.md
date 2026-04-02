## 1. Domain Layer — DomainError + ErrorCode

- [x] 1.1 Create `domain/error.py` with `ErrorCode` enum and `DomainError` exception class
- [x] 1.2 Replace `ValueError` raises in `domain/block/model.py` with `DomainError(ErrorCode.VALIDATION, ...)`
- [x] 1.3 Replace `ValueError` raises in `domain/service/model.py` with `DomainError(ErrorCode.VALIDATION, ...)`
- [x] 1.4 Replace `ValueError` raises in `domain/station/model.py` with `DomainError(ErrorCode.VALIDATION, ...)`
- [x] 1.5 Replace `ValueError` raises in `domain/domain_service/route_finder.py` — use `ErrorCode.NO_ROUTE` for "No route" and `ErrorCode.VALIDATION` for others
- [x] 1.6 Update domain unit tests to assert `DomainError` instead of `ValueError`

## 2. Application Layer — ConflictError + Service Errors

- [x] 2.1 Make `ConflictError` a subclass of `DomainError` with `ErrorCode.CONFLICT` (update `application/service/errors.py`)
- [x] 2.2 Replace `ValueError` raises in `application/service/service.py` with `DomainError(ErrorCode.NOT_FOUND, ...)` and `DomainError(ErrorCode.VALIDATION, ...)`
- [x] 2.3 Replace `ValueError` raises in `application/block/service.py` with `DomainError(ErrorCode.NOT_FOUND, ...)`
- [x] 2.4 Update application integration tests to assert `DomainError` instead of `ValueError`

## 3. API Layer — Exception Handler + Route Cleanup

- [x] 3.1 Create `api/error_handler.py` with `ErrorCode → HTTP status` mapping and `domain_error_handler` function (including conflict detail builder)
- [x] 3.2 Register `domain_error_handler` in `main.py` via `app.add_exception_handler`
- [x] 3.3 Remove try/except blocks from `api/service/routes.py` and delete `_conflict_response` helper
- [x] 3.4 Remove try/except blocks from `api/block/routes.py`
- [x] 3.5 Remove try/except blocks from `api/route/routes.py`
- [x] 3.6 Update API tests to verify correct HTTP status codes still returned for all error scenarios

## 4. Verification

- [x] 4.1 Grep for remaining `raise ValueError` in domain/ and application/ — should be zero
- [x] 4.2 Run full test suite (`uv run pytest`) and confirm all pass

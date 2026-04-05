## 1. Domain Layer — DomainError + error_code + context

- [x] 1.1 Update `DomainError.__init__` in `domain/error.py` to accept `error_code: str` and `context: dict | None = None`
- [x] 1.2 Add error_code + context to raise sites in `domain/domain_service/route_finder.py` (NO_ROUTE_BETWEEN_STOPS with from/to stop IDs, SAME_ORIGIN_DESTINATION with stop_id, INSUFFICIENT_STOPS)
- [x] 1.3 Add error_code + context to raise sites in `domain/domain_service/route_builder.py` (STOP_NOT_FOUND with stop_id, UNKNOWN_NODE with node_id, ENTRY_NODE_NOT_IN_ROUTE with node_id)
- [x] 1.4 Add error_code to raise sites in `domain/service/model.py` and `domain/block/model.py` and `domain/station/model.py` (internal invariants — no context needed)

## 2. Application Layer — error_code + context at raise sites

- [x] 2.1 Add error_code + context to raise sites in `application/service/service.py` (EMPTY_SERVICE_NAME, VEHICLE_NOT_FOUND with vehicle_id, SERVICE_NOT_FOUND with service_id)
- [x] 2.2 Update `ConflictError.__init__` in `application/service/errors.py` to pass error_code="SCHEDULING_CONFLICT"
- [x] 2.3 Add error_code + context to raise sites in `application/schedule/schedule_service.py` (INSUFFICIENT_VEHICLES with needed/available, SCHEDULE_INFEASIBLE, INVALID_INTERVAL, INVALID_DWELL_TIME, INVALID_TIME_RANGE)
- [x] 2.4 Add error_code + context to raise site in `application/block/service.py` (BLOCK_NOT_FOUND with block_id)

## 3. API Layer — Structured error response

- [x] 3.1 Add `ErrorDetail` model and update `ErrorResponse` in `api/shared/schemas.py`
- [x] 3.2 Update `domain_error_handler` in `api/error_handler.py` to return structured detail with error_code, message, context
- [x] 3.3 Add `responses={**VALIDATION_RESPONSE}` to `POST /api/schedules/generate` route
- [x] 3.4 Update error handler tests in `tests/api/test_error_handler.py`

## 4. Verify

- [x] 4.1 Run full test suite and confirm all tests pass
- [x] 4.2 Run linter and confirm no violations

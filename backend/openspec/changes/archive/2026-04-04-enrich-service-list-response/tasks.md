## 1. API Schema

- [x] 1.1 Add `start_time: int | None`, `origin_name: str | None`, `destination_name: str | None` fields to `ServiceResponse` in `api/service/schemas.py`
- [x] 1.2 Update `ServiceResponse.from_domain()` to derive the three fields from the `Service` domain object's route and timetable

## 2. Tests

- [x] 2.1 Add/update unit tests for `ServiceResponse.from_domain()` covering: service with route+timetable, service with empty route
- [x] 2.2 Update application-layer `list_services` test to assert new fields are present in the response
- [x] 2.3 Update API integration test for `GET /api/services` to verify new fields in JSON response

## 3. Verification

- [x] 3.1 Run full test suite and confirm all existing tests still pass
- [x] 3.2 Run linter (`ruff check`, `ruff format --check`, `lint-imports`) and fix any issues

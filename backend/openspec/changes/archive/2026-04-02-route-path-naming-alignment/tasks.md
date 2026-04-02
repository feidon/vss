## 1. Domain Layer

- [x] 1.1 Rename `Service.path` field to `route` in `domain/service/model.py`
- [x] 1.2 Rename `path` parameter to `route` in `Service.update_route()` method
- [x] 1.3 Update `_validate_entries_in_path` to `_validate_entries_in_route` and its `path` parameter
- [x] 1.4 Update `_validate_connectivity` parameter name from `path` to `route`
- [x] 1.5 Update validation error messages: "not in path" -> "not in route", "Path must contain" -> "Route must contain"
- [x] 1.6 Update domain tests in `tests/domain/test_service.py` to use `route` field name and updated error messages

## 2. Application Layer

- [x] 2.1 Rename `RouteValidationResult.path` to `route` in `application/service/dto.py`
- [x] 2.2 Update `ServiceAppService` references from `.path` to `.route` in `application/service/service.py`
- [x] 2.3 Update application tests (`tests/application/test_update_route.py`, `tests/application/test_validate_route.py`) to use `.route`

## 3. Infrastructure Layer

- [x] 3.1 Rename DB column from `path` to `route` in `services_table` definition (`infra/postgres/tables.py`)
- [x] 3.2 Update `PostgresServiceRepository._to_entity()` to read from `row["route"]` and pass as `route=` kwarg
- [x] 3.3 Update `PostgresServiceRepository._to_table_without_id()` to key JSONB data as `"route"`
- [x] 3.4 Update seed data if it references `path` field (`infra/seed.py`, `infra/postgres/seed.py`)
- [x] 3.5 Update infra tests (`tests/infra/test_postgres_service_repo.py`) to use `route` field

## 4. API Layer

- [x] 4.1 Rename `ServiceDetailResponse.path` to `route` in `api/service/schemas.py`
- [x] 4.2 Update `ServiceDetailResponse.from_domain()` local variable `path_nodes` -> `route_nodes` and field assignment
- [x] 4.3 Rename `ValidateRouteResponse.path` to `route` in `api/route/schemas.py`
- [x] 4.4 Update API route handlers if they reference `.path` on results (`api/service/routes.py`, `api/route/routes.py`)
- [x] 4.5 Update API tests (`tests/api/test_service_routes.py`, `tests/api/test_route_routes.py`) to expect `route` in JSON responses

## 5. Cross-cutting Verification

- [x] 5.1 Grep for remaining `\.path` and `"path"` references in service-related code to catch any missed occurrences
- [x] 5.2 Run full test suite (`uv run pytest`) and verify all tests pass
- [x] 5.3 Run PostgreSQL integration tests (`uv run pytest -m postgres`) if DB is available

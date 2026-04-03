## 1. Domain Interface

- [x] 1.1 Replace `save()` with `create(service: Service) -> Service` and `update(service: Service) -> None` in `domain/service/repository.py`

## 2. Implementations

- [x] 2.1 Implement `create()` and `update()` in `infra/postgres/service_repo.py` — `create()` returns new Service with DB-assigned ID, `update()` runs UPDATE statement
- [x] 2.2 Implement `create()` and `update()` in `tests/fakes/service_repo.py` — `create()` returns new Service with counter-assigned ID

## 3. Call Sites

- [x] 3.1 Update `ServiceAppService.create_service()` to call `create()` and use the returned entity
- [x] 3.2 Update `ServiceAppService.update_service_route()` to call `update()`

## 4. Tests

- [x] 4.1 Update `tests/infra/test_postgres_service_repo.py` — rename test methods and assertions for `create()`/`update()`
- [x] 4.2 Update `tests/application/test_service_service.py` — adjust for new method names and return semantics (no changes needed — tests use app service, not repo directly)
- [x] 4.3 Run full test suite and verify all tests pass

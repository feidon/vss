## Why

The current `ServiceRepository.save()` conflates creation and update into a single method that checks `service.id is None` to decide behavior. This violates the explicit-over-implicit principle, hides intent at call sites, and forces the create path to mutate the entity by assigning the generated ID — breaking the project's immutability rule.

## What Changes

- **BREAKING**: Replace `ServiceRepository.save(service)` with two explicit methods:
  - `create(service) -> Service` — inserts a new service, returns a new entity with the assigned ID (no mutation)
  - `update(service) -> None` — updates an existing service (ID must already be set)
- Update `ServiceAppService.create_service()` to call `create()` and use the returned entity
- Update `ServiceAppService.update_service_route()` to call `update()`
- Update `PostgresServiceRepository` implementation accordingly
- Update `InMemoryServiceRepository` test double
- Update all tests referencing `save()`

## Capabilities

### New Capabilities

_(none — this is a refactoring of existing capability)_

### Modified Capabilities

_(no existing specs to modify)_

## Impact

- `domain/service/repository.py` — interface change
- `infra/postgres/service_repo.py` — implementation split
- `tests/fakes/service_repo.py` — test double update
- `application/service/service.py` — call site updates
- `tests/` — test updates for new method names and return types
- No API or schema changes — purely internal refactoring

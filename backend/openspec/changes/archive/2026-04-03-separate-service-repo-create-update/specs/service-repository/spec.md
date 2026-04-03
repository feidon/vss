## ADDED Requirements

### Requirement: Repository provides separate create and update methods
The `ServiceRepository` SHALL expose `create(service: Service) -> Service` for inserting new services and `update(service: Service) -> None` for updating existing services. The `save()` method SHALL be removed.

#### Scenario: Creating a new service
- **WHEN** `create()` is called with a Service that has no ID
- **THEN** the service is persisted to storage and a new Service instance with the assigned ID is returned

#### Scenario: Updating an existing service
- **WHEN** `update()` is called with a Service that has an ID
- **THEN** the service's fields are updated in storage

#### Scenario: Create does not mutate input
- **WHEN** `create()` is called with a Service
- **THEN** the input Service object SHALL NOT be mutated; a new instance is returned instead

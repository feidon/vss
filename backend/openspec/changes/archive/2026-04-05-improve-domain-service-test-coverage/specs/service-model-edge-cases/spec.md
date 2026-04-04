## ADDED Requirements

### Requirement: Service equality with None id uses identity
When a Service has `id=None`, equality SHALL fall back to object identity (`is`), not value comparison.

#### Scenario: Two services with None id are not equal
- **WHEN** two Service instances are created with `id=None` and identical fields
- **THEN** they SHALL NOT be equal (different objects)

#### Scenario: Same service with None id equals itself
- **WHEN** a Service with `id=None` is compared to itself
- **THEN** it SHALL be equal

### Requirement: Service hash with None id uses object identity hash
When a Service has `id=None`, `__hash__` SHALL return `id(self)` so each instance is distinct in sets/dicts.

#### Scenario: Two None-id services in a set
- **WHEN** two Service instances with `id=None` are added to a set
- **THEN** the set SHALL contain 2 elements

### Requirement: Service equality with mixed None and non-None id
When comparing a Service with `id=None` to one with a non-None id, they SHALL NOT be equal.

#### Scenario: None id vs numeric id
- **WHEN** a Service with `id=None` is compared to a Service with `id=1`
- **THEN** they SHALL NOT be equal

### Requirement: Service update_route validates connectivity for empty route
`update_route` with an empty route SHALL raise DomainError.

#### Scenario: Empty route rejected
- **WHEN** `update_route` is called with `route=[]` and `timetable=[]` and any connections
- **THEN** a DomainError SHALL be raised with "at least one node" message

### Requirement: Service update_route validates connectivity for single node
`update_route` with a single-node route and matching timetable SHALL succeed (no connectivity check needed for 1 node).

#### Scenario: Single node route accepted
- **WHEN** `update_route` is called with a 1-node route, matching timetable entry, and any connections
- **THEN** the route SHALL be updated successfully

### Requirement: Service creation with non-Service type returns NotImplemented
Comparing a Service to a non-Service object SHALL return False.

#### Scenario: Service compared to string
- **WHEN** a Service is compared via `==` to a string
- **THEN** the result SHALL be False

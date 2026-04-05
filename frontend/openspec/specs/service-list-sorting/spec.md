### Requirement: Service list sorted by start time ascending
The schedule list page SHALL display services sorted by `start_time` in ascending order (earliest first).

#### Scenario: Services with different start times
- **WHEN** the service list contains services with start times 1700000060, 1700000000, and 1700000030
- **THEN** the list SHALL display them in order: 1700000000, 1700000030, 1700000060

#### Scenario: All services have the same start time
- **WHEN** the service list contains multiple services with identical start times
- **THEN** the list SHALL display all services (order among ties is unspecified)

### Requirement: Services without start time appear last
Services with a null `start_time` SHALL appear after all services that have a start time.

#### Scenario: Mix of services with and without start times
- **WHEN** the service list contains services where some have `start_time` values and others have `start_time` as null
- **THEN** services with a numeric `start_time` SHALL appear first (sorted ascending), followed by services with null `start_time`

#### Scenario: All services have null start time
- **WHEN** every service in the list has `start_time` as null
- **THEN** the list SHALL display all services (order is unspecified)

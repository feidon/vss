## ADDED Requirements

### Requirement: Vehicle charging during idle time
The system SHALL charge a vehicle's battery during idle time between consecutive services. The charging rate is 1% per 12 seconds of idle time. Battery MUST NOT exceed 100%.

#### Scenario: Sufficient idle time to fully charge
- **WHEN** a vehicle has 60% battery and 600 seconds of idle time between services
- **THEN** the battery after charging is min(60 + 600 // 12, 100) = min(110, 100) = 100%

#### Scenario: Partial charge during short idle
- **WHEN** a vehicle has 70% battery and 60 seconds of idle time
- **THEN** the battery after charging is 70 + 60 // 12 = 75%

### Requirement: Minimum departure charge threshold
The system SHALL require a vehicle to have at least 80% battery before departing on a service. If the battery is below 80% after charging during idle time, an `InsufficientChargeConflict` MUST be raised.

#### Scenario: Vehicle departs with sufficient charge
- **WHEN** a vehicle has 85% battery before a service
- **THEN** no insufficient-charge conflict is raised and the service proceeds

#### Scenario: Idle time insufficient to reach departure threshold
- **WHEN** a vehicle finishes a service at 50% battery and has 200 seconds idle before the next service
- **THEN** the battery after charging is 50 + 200 // 12 = 66%, which is below 80%, and an `InsufficientChargeConflict` is raised identifying the two services

#### Scenario: Vehicle exactly at departure threshold
- **WHEN** a vehicle has exactly 80% battery before departing
- **THEN** no insufficient-charge conflict is raised (80% meets the threshold)

### Requirement: Insufficient charge conflicts included in service validation
The system SHALL detect insufficient-charge conflicts as part of the existing `validate_service()` pipeline. Insufficient-charge conflicts MUST be returned alongside all other conflict types.

#### Scenario: Route update blocked by insufficient charge
- **WHEN** a route update is submitted and the vehicle cannot charge to 80% between two of its services
- **THEN** the API returns 409 with a response body containing `insufficient_charge_conflicts`

### Requirement: Conflict identifies both services
An `InsufficientChargeConflict` MUST identify both the preceding service (that drained the battery) and the following service (that cannot depart).

#### Scenario: Conflict references service pair
- **WHEN** an insufficient-charge conflict is detected between service A and service B
- **THEN** the conflict object contains `service_a_id` (preceding) and `service_b_id` (following)

## MODIFIED Requirements

### Requirement: Minimum departure charge threshold
The system SHALL require a vehicle to have at least 80% battery before departing on a service. If the battery is below 80% after charging during idle time, an `InsufficientChargeConflict` MUST be raised. The departure threshold check SHALL only apply when the vehicle has a subsequent departure. When a vehicle returns to the Yard as the final stop across all its services, the system MUST NOT check the departure threshold — the vehicle is parked and will charge indefinitely.

#### Scenario: Vehicle departs with sufficient charge
- **WHEN** a vehicle has 85% battery before a service
- **THEN** no insufficient-charge conflict is raised and the service proceeds

#### Scenario: Idle time insufficient to reach departure threshold
- **WHEN** a vehicle finishes a service at 50% battery and has 200 seconds idle before the next service
- **THEN** the battery after charging is 50 + 200 // 12 = 66%, which is below 80%, and an `InsufficientChargeConflict` is raised identifying the two services

#### Scenario: Vehicle exactly at departure threshold
- **WHEN** a vehicle has exactly 80% battery before departing
- **THEN** no insufficient-charge conflict is raised (80% meets the threshold)

#### Scenario: Vehicle returns to Yard as final stop with low battery
- **WHEN** a vehicle completes a round trip ending at the Yard with battery below 80% and there are no subsequent services for this vehicle
- **THEN** no insufficient-charge conflict is raised because the vehicle does not need to depart again

#### Scenario: Vehicle returns to Yard but has a subsequent service
- **WHEN** a vehicle returns to the Yard with 50% battery and a subsequent service departs 100 seconds later
- **THEN** the battery after charging is 50 + 100 // 12 = 58%, which is below 80%, and an `InsufficientChargeConflict` is raised

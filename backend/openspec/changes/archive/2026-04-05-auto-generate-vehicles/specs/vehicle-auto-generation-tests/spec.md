## ADDED Requirements

### Requirement: VehicleRepository.add_by_number creates vehicles with sequential names
The `add_by_number(n)` method SHALL create exactly `n` new `Vehicle` entities. Each new vehicle SHALL be named `V{N}` where N is the 0-based index offset by the current vehicle count. Each vehicle SHALL have a unique `uuid7` ID.

#### Scenario: Add vehicles to empty repository
- **WHEN** repository contains 0 vehicles and `add_by_number(3)` is called
- **THEN** repository contains 3 vehicles named V0, V1, V2

#### Scenario: Add vehicles to pre-populated repository
- **WHEN** repository contains 2 vehicles (V0, V1) and `add_by_number(2)` is called
- **THEN** repository contains 4 vehicles total, with the new ones named V2, V3

#### Scenario: Add zero vehicles
- **WHEN** `add_by_number(0)` is called
- **THEN** no new vehicles are created and existing vehicles are unchanged

### Requirement: PostgresVehicleRepository.add_by_number awaits async calls
The Postgres implementation of `add_by_number` SHALL properly `await` all async method calls, including `self.find_all()`.

#### Scenario: add_by_number persists to database
- **WHEN** `add_by_number(2)` is called on the Postgres repository
- **THEN** 2 new vehicle rows exist in the `vehicles` table and are retrievable via `find_all()`

### Requirement: ScheduleAppService auto-generates vehicles when insufficient
When the computed vehicle requirement exceeds the number of existing vehicles, `ScheduleAppService.generate()` SHALL call `VehicleRepository.add_by_number(deficit)` to create the missing vehicles before proceeding with schedule generation.

#### Scenario: Generate schedule with zero pre-existing vehicles
- **WHEN** no vehicles exist in the repository and `generate()` is called
- **THEN** the service creates the required number of vehicles and the response `vehicles_used` matches the computed requirement

#### Scenario: Generate schedule with fewer vehicles than needed
- **WHEN** 1 vehicle exists but the schedule requires 2+
- **THEN** the service creates additional vehicles to meet the requirement and successfully generates services

#### Scenario: Generate schedule with sufficient vehicles
- **WHEN** enough vehicles already exist in the repository
- **THEN** no new vehicles are created and the existing vehicles are used

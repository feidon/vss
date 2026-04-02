## ADDED Requirements

### Requirement: Backend vehicles endpoint
The backend SHALL expose `GET /vehicles` returning a JSON array of `{ id: UUID, name: string }` objects representing all available vehicles.

#### Scenario: Fetch all vehicles
- **WHEN** a client sends `GET /vehicles`
- **THEN** the response status is 200 and the body is a JSON array of all seeded vehicles (V1, V2, V3)

### Requirement: VehicleService
The system SHALL provide `VehicleService` in `core/services/` with method `getVehicles(): Observable<Vehicle[]>` calling `GET /vehicles`.

#### Scenario: Fetch vehicle list
- **WHEN** `vehicleService.getVehicles()` is subscribed
- **THEN** it performs `GET http://localhost:8000/vehicles` and emits a typed `Vehicle[]`

### Requirement: Schedule editor loads vehicles from VehicleService
The `ScheduleEditorComponent` SHALL load vehicles by calling `VehicleService.getVehicles()` in `ngOnInit` instead of extracting them from `GraphService.getGraph()`.

#### Scenario: Vehicles populate the create form dropdown
- **WHEN** the schedule editor page loads
- **THEN** the vehicle dropdown in the service creation form contains all available vehicles (V1, V2, V3)

#### Scenario: Vehicles load independently of services
- **WHEN** no services exist yet and the user navigates to the schedule editor
- **THEN** the vehicle dropdown still shows all available vehicles

## ADDED Requirements

### Requirement: VehicleService
The system SHALL provide `VehicleService` in `core/services/` with method `getVehicles(): Observable<Vehicle[]>` calling `GET /vehicles`.

#### Scenario: Fetch vehicle list
- **WHEN** `vehicleService.getVehicles()` is subscribed
- **THEN** it performs `GET http://localhost:8000/vehicles` and emits a typed `Vehicle[]`

## MODIFIED Requirements

### Requirement: ServiceService
The system SHALL provide `ServiceService` in `core/services/` with methods:
- `getServices(): Observable<ServiceResponse[]>` — calls `GET /services`, returns list summary (id, name, vehicle_id only)
- `getService(id: number): Observable<ServiceDetailResponse>` — calls `GET /services/{id}`, returns full detail with `route`, `timetable`, and `graph`
- `createService(request: CreateServiceRequest): Observable<ServiceIdResponse>` — calls `POST /services`
- `updateRoute(id: number, request: UpdateRouteRequest): Observable<ServiceIdResponse>` — calls `PATCH /services/{id}/route`
- `deleteService(id: number): Observable<void>` — calls `DELETE /services/{id}`

#### Scenario: List services returns summary only
- **WHEN** `serviceService.getServices()` is subscribed
- **THEN** it performs `GET http://localhost:8000/services` and emits `ServiceResponse[]` where each item contains only `id`, `name`, `vehicle_id`

#### Scenario: Get service detail returns full response with graph
- **WHEN** `serviceService.getService(101)` is subscribed
- **THEN** it performs `GET http://localhost:8000/services/101` and emits `ServiceDetailResponse` containing `id`, `name`, `vehicle_id`, `route`, `timetable`, and `graph`

#### Scenario: Update route sends node_id in stops
- **WHEN** `serviceService.updateRoute(id, { stops: [{ node_id, dwell_time }], start_time })` is subscribed
- **THEN** the request body uses `node_id` (not `platform_id`) for each stop

#### Scenario: Update route returns conflict on 409
- **WHEN** `serviceService.updateRoute(id, request)` receives a 409 response
- **THEN** the error propagates to the subscriber with correctly shaped conflict types

#### Scenario: Delete a service
- **WHEN** `serviceService.deleteService(101)` is subscribed
- **THEN** it performs `DELETE http://localhost:8000/services/101` and completes

### Requirement: GraphService
The system SHALL provide `GraphService` in `core/services/` with method `getGraph(): Observable<GraphResponse>` calling `GET /graph`.

#### Scenario: Fetch graph data
- **WHEN** `graphService.getGraph()` is subscribed
- **THEN** it performs `GET http://localhost:8000/graph` and emits a typed `GraphResponse`

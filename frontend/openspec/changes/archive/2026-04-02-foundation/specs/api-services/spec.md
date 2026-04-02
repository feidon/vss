## ADDED Requirements

### Requirement: GraphService
The system SHALL provide `GraphService` in `core/services/` with method `getGraph(): Observable<GraphResponse>` calling `GET /graph`.

#### Scenario: Fetch graph data
- **WHEN** `graphService.getGraph()` is subscribed
- **THEN** it performs `GET http://localhost:8000/graph` and emits a typed `GraphResponse`

### Requirement: BlockService
The system SHALL provide `BlockService` in `core/services/` with methods:
- `getBlocks(): Observable<BlockResponse[]>` — calls `GET /blocks`
- `updateBlock(id: string, request: UpdateBlockRequest): Observable<BlockIdResponse>` — calls `PATCH /blocks/{id}`

#### Scenario: Fetch all blocks
- **WHEN** `blockService.getBlocks()` is subscribed
- **THEN** it performs `GET http://localhost:8000/blocks` and emits `BlockResponse[]`

#### Scenario: Update block traversal time
- **WHEN** `blockService.updateBlock(id, { traversal_time_seconds: 60 })` is subscribed
- **THEN** it performs `PATCH http://localhost:8000/blocks/{id}` with JSON body and emits `BlockIdResponse`

### Requirement: ServiceService
The system SHALL provide `ServiceService` in `core/services/` with methods:
- `getServices(): Observable<ServiceResponse[]>` — calls `GET /services`
- `getService(id: number): Observable<ServiceResponse>` — calls `GET /services/{id}`
- `createService(request: CreateServiceRequest): Observable<ServiceIdResponse>` — calls `POST /services`
- `updateRoute(id: number, request: UpdateRouteRequest): Observable<ServiceIdResponse>` — calls `PATCH /services/{id}/route`
- `deleteService(id: number): Observable<void>` — calls `DELETE /services/{id}`

#### Scenario: Create a service
- **WHEN** `serviceService.createService({ name: 'S101', vehicle_id: 'uuid' })` is subscribed
- **THEN** it performs `POST http://localhost:8000/services` with JSON body and emits `ServiceIdResponse`

#### Scenario: Update route returns conflict on 409
- **WHEN** `serviceService.updateRoute(id, request)` receives a 409 response
- **THEN** the error propagates to the subscriber (feature components handle conflict display)

#### Scenario: Delete a service
- **WHEN** `serviceService.deleteService(101)` is subscribed
- **THEN** it performs `DELETE http://localhost:8000/services/101` and completes

### Requirement: Base URL configuration
All services SHALL use `http://localhost:8000` as the base URL, defined as a single constant importable from `core/services/`.

#### Scenario: Base URL consistency
- **WHEN** any service makes an HTTP request
- **THEN** the URL starts with the configured base URL constant

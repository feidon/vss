## ADDED Requirements

### Requirement: ScheduleService provides generate method
A `ScheduleService` in `core/services/` SHALL expose a `generate(request: GenerateScheduleRequest): Observable<GenerateScheduleResponse>` method that calls `POST /api/schedules/generate`.

#### Scenario: Successful API call
- **WHEN** `generate()` is called with valid parameters
- **THEN** it SHALL send a POST to `{baseUrl}/schedules/generate` with the request body and return the parsed response as `GenerateScheduleResponse`

#### Scenario: Error propagation
- **WHEN** the backend returns an error status
- **THEN** the observable SHALL emit the error for the caller to handle

### Requirement: Generate schedule request model
The system SHALL define a `GenerateScheduleRequest` interface with fields: `interval_seconds: number`, `start_time: number`, `end_time: number`, `dwell_time_seconds: number`.

#### Scenario: Interface matches backend schema
- **WHEN** a request is constructed
- **THEN** it SHALL contain exactly the four fields expected by `POST /api/schedules/generate`

### Requirement: Generate schedule response model
The system SHALL define a `GenerateScheduleResponse` interface with fields: `services_created: number`, `vehicles_used: string[]`, `cycle_time_seconds: number`.

#### Scenario: Interface matches backend response
- **WHEN** a response is received
- **THEN** it SHALL be typed with `services_created` (number), `vehicles_used` (UUID string array), and `cycle_time_seconds` (number)

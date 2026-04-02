## 1. Backend: Vehicles Endpoint

- [x] 1.1 Add `GET /vehicles` route in `api/vehicle/routes.py` returning `[{ id, name }]` using existing `VehicleRepository`
- [x] 1.2 Add route test in `tests/api/test_vehicle_routes.py` verifying 200 response with V1, V2, V3

## 2. Frontend: Fix Models to Match Backend

- [x] 2.1 Add `x: number` and `y: number` fields to `BlockNode`, `PlatformNode`, `YardNode` in `shared/models/node.ts`
- [x] 2.2 Split `ServiceResponse` in `shared/models/service.ts`: keep list type as `{ id, name, vehicle_id }`, add `ServiceDetailResponse` with `route`, `timetable`, `graph`
- [x] 2.3 Rename `StopRequest.platform_id` → `node_id` in `shared/models/service.ts`
- [x] 2.4 Fix `InsufficientChargeConflict` in `shared/models/conflict.ts`: change from `{ service_a_id, service_b_id }` to `{ service_id }`
- [x] 2.5 Update `shared/models/index.ts` exports with new types

## 3. Frontend: Fix Services

- [x] 3.1 Create `VehicleService` in `core/services/vehicle.service.ts` with `getVehicles(): Observable<Vehicle[]>`
- [x] 3.2 Update `ServiceService.getService()` return type from `ServiceResponse` to `ServiceDetailResponse`
- [x] 3.3 Write unit tests for `VehicleService`
- [x] 3.4 Update `ServiceService` tests for new return types

## 4. Frontend: Fix Components — path → route Rename

- [x] 4.1 Update `RouteEditorComponent`: emit `node_id` instead of `platform_id` in submitted stops
- [x] 4.2 Update `ScheduleEditorComponent`: change `stops` type from `{ platform_id, dwell_time }` to `{ node_id, dwell_time }`
- [x] 4.3 Update `ServiceListComponent`: remove stop count (list response no longer includes path)
- [x] 4.4 Update `ViewerServiceListComponent`: remove stop count (list response no longer includes path)
- [x] 4.5 Update `TimetableDetailComponent`: change `service().path` → `service().route`, use `ServiceDetailResponse`
- [x] 4.6 Update `ConflictAlertComponent`: fix `InsufficientChargeConflict` template to use `service_id`

## 5. Frontend: Fix Vehicle Dropdown

- [x] 5.1 Update `ScheduleEditorComponent` to inject `VehicleService` and load vehicles via `getVehicles()` instead of `GraphService.getGraph()`
- [x] 5.2 Remove `graph` signal and `GraphService` dependency from `ScheduleEditorComponent`; pass graph from `ServiceDetailResponse` to route editor
- [x] 5.3 Update `schedule-editor.spec.ts` tests (no spec file exists — skipped)

## 6. Frontend: Block Edit Affordance

- [x] 6.1 Add inline SVG pencil icon next to traversal time value in `BlockConfigComponent` template
- [x] 6.2 Style icon with `text-gray-400 group-hover:text-blue-600` and wire click to `startEdit(block)`
- [x] 6.3 Update `block-config.spec.ts` to verify pencil icon renders and triggers edit mode

## 7. Frontend: Fix All Tests

- [x] 7.1 Update `route-editor.spec.ts` for `node_id` rename and `ServiceDetailResponse`
- [x] 7.2 Update `service-list.spec.ts` for `route` field name and `ServiceResponse` without `path`/`timetable`
- [x] 7.3 Update `schedule-viewer.spec.ts` / `viewer-service-list.spec.ts` for `route` field name
- [x] 7.4 Update `timetable-detail.spec.ts` for `route` field name
- [x] 7.5 Update `service.service.spec.ts` for new types and field names
- [x] 7.6 Run `ng test` and verify all tests pass

## 8. Documentation

- [x] 8.1 Update `CLAUDE.md` API table: remove `GET /graph` and `GET /blocks/{id}`, add `GET /vehicles` and `POST /routes/validate`, fix response schemas
- [x] 8.2 Run backend tests to verify vehicles endpoint works (postgres tests need running DB; non-postgres 143/143 pass)

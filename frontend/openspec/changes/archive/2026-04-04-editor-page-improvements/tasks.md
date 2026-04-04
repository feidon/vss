## 1. Diagnose and fix initial state loading

- [x] 1.1 Debug `RouteEditorComponent.deriveInitialState()` — add temporary logging to verify the effect fires and `service().route` / `service().timetable` contain data when entering an existing service
- [x] 1.2 Fix the stop queue population: ensure `stops` signal is set with non-block nodes from `service.route`, each with `dwellTime = departure - arrival` from the matching timetable entry
- [x] 1.3 Fix the start time population: ensure `startTimeLocal` signal is set from `timetable[0].arrival` converted to datetime-local format
- [x] 1.4 If the `effect()` approach is the root cause, replace with `ngOnInit` or explicit `linkedSignal`/`computed` to ensure initialization runs reliably with `input.required()` signals

## 2. Diagnose and fix conflict message display

- [x] 2.1 Debug the 409 error handling — verify `err.error.detail` matches the `ConflictResponse` interface shape (check for nesting: `err.error` vs `err.error.detail`)
- [x] 2.2 Fix the conflict signal assignment in `ScheduleEditorComponent.onRouteSubmitted()` so `conflicts()` is set correctly from the 409 response body
- [x] 2.3 Verify `ConflictAlertComponent` renders without errors when all conflict arrays are present (including empty arrays for unused conflict types)

## 3. Testing

- [x] 3.1 Write/update test for `RouteEditorComponent`: verify stops and start time are populated when service input has existing route and timetable
- [x] 3.2 Write/update test for `ScheduleEditorComponent`: verify conflict signal is set when `updateRoute` returns 409
- [x] 3.3 Manual verification: create a service with a route, navigate away, navigate back — confirm stops and start time are pre-filled
- [x] 3.4 Manual verification: submit a conflicting route update — confirm conflict alert appears with details

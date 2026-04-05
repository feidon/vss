## 1. Shared Models & Utilities

- [x] 1.1 Add `ErrorDetail` interface to `shared/models/` and export it from the barrel file
- [x] 1.2 Extend `extractErrorMessage` in `error-utils.ts` to accept an optional `nameMap: ReadonlyMap<string, string>` parameter and substitute context UUIDs in the message
- [x] 1.3 Add a `buildNameMap` helper function in `error-utils.ts` that builds a `Map<string, string>` from arrays of `{ id, name }` objects
- [x] 1.4 Write tests for `extractErrorMessage`: structured detail with name map, structured detail without name map, legacy string detail, 5xx error, multiple context substitutions, unknown UUID fallback

## 2. Schedule Editor Error Handling

- [x] 2.1 Update `ScheduleEditorComponent.onRouteSubmitted` error handler to build a name map from `service().graph` (nodes, edges, vehicles) and pass it to `extractErrorMessage`
- [x] 2.2 Update `ScheduleEditorComponent.ngOnInit` error handler to pass name map when service is loaded (fallback: no map if service not yet loaded)
- [x] 2.3 Write tests for schedule editor error handling with structured errors and name resolution

## 3. Create Service Dialog Error Handling

- [x] 3.1 Update `CreateServiceDialogComponent.onSubmit` error handler to build a name map from `vehicles()` and pass it to `extractErrorMessage`
- [x] 3.2 Write test for create service dialog error handling with structured error and vehicle name resolution

## 4. Block Config Error Handling

- [x] 4.1 Update `BlockConfigComponent.save` error handler to build a name map from `blocks()` and pass it to `extractErrorMessage`
- [x] 4.2 Write test for block config error handling with structured error and block name resolution

## 5. Schedule List Error Handling

- [x] 5.1 Update `ScheduleListComponent` error handlers to pass through structured messages (no name map needed — errors here are generic load/delete failures)
- [x] 5.2 Verify existing tests still pass with the updated `extractErrorMessage` signature

## 6. Verification

- [x] 6.1 Run full test suite (`ng test`) and fix any failures
- [x] 6.2 Run lint (`ng lint`) and format check (`npx prettier --check "src/**/*.{ts,html,css}"`)
- [ ] 6.3 Manual smoke test: trigger a 400/404/422 error in the schedule editor and verify the message shows names instead of UUIDs

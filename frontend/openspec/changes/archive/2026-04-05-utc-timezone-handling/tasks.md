## 1. TimeUtils — Shared Utility

- [x] 1.1 Create `src/app/shared/utils/time-utils.ts` with three pure functions: `localDatetimeToEpoch`, `epochToLocalDatetime`, `epochToDisplayTime`
- [x] 1.2 Create `src/app/shared/utils/time-utils.spec.ts` with unit tests: round-trip consistency, zero/null handling (em dash), padding, all three functions

## 2. EpochTimePipe — Delegate to TimeUtils

- [x] 2.1 Update `EpochTimePipe.transform()` to call `epochToDisplayTime()` instead of inline `Date` logic
- [x] 2.2 Update `epoch-time.pipe.spec.ts` to verify pipe delegates to `epochToDisplayTime`

## 3. RouteEditorComponent — Use TimeUtils

- [x] 3.1 Replace `onSubmit()` inline epoch conversion with `localDatetimeToEpoch()`
- [x] 3.2 Replace `deriveInitialState()` inline datetime formatting with `epochToLocalDatetime()`
- [x] 3.3 Remove `formatTime()` method, import `EpochTimePipe`, use `| epochTime` pipe in timetable template
- [x] 3.4 Update `route-editor.spec.ts` to cover the new conversion paths

## 4. ConflictAlertComponent — Use EpochTimePipe

- [x] 4.1 Remove `formatTime()` method, import `EpochTimePipe`, use `| epochTime` pipe for overlap times in template
- [x] 4.2 Verify conflict-alert rendering in existing tests (or add test if none exists)

## 5. Verification

- [x] 5.1 Run full test suite (`ng test`), ensure all pass
- [x] 5.2 Run lint and format checks (`ng lint` + `npx prettier --check`)

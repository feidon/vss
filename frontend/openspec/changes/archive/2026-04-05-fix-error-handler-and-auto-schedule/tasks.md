## 1. Fix conflict response parsing

- [x] 1.1 In `schedule-editor.ts` `saveRoute()`, change `err.error?.detail?.context` to `err.error?.detail` and update the type guard to check properties on `detail` directly
- [x] 1.2 Verify `ConflictResponse` interface in `shared/models/conflict.ts` matches the `detail` object shape (fields: `vehicle_conflicts`, `block_conflicts`, `interlocking_conflicts`, `battery_conflicts`)

## 2. Fix auto-schedule button label

- [x] 2.1 In `schedule-list.ts`, change button text from "Auto Schedule" to "Auto-Generate Schedule"

## 3. Verify

- [x] 3.1 Run `ng build` to confirm no compilation errors
- [x] 3.2 Run `ng test` to confirm no test regressions

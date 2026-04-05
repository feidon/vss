## 1. Models & API Service

- [x] 1.1 Add `GenerateScheduleRequest` and `GenerateScheduleResponse` interfaces to `src/app/shared/models/schedule.ts`
- [x] 1.2 Create `ScheduleService` in `src/app/core/services/schedule.service.ts` with `generate()` method calling `POST /api/schedules/generate`

## 2. Auto Schedule Dialog Component

- [x] 2.1 Create `AutoScheduleDialogComponent` in `src/app/features/schedule/auto-schedule-dialog.ts` with form (interval, start time, end time, dwell time), destructive warning banner, validation, loading state, error display, and success summary view
- [x] 2.2 Wire the dialog result: on success, return generation result; on cancel, return undefined

## 3. Schedule List Integration

- [x] 3.1 Add "Auto Schedule" button to `ScheduleListComponent` header next to "Create Service"
- [x] 3.2 Add `onAutoSchedule()` method that opens `AutoScheduleDialogComponent` and refreshes the service list on successful generation

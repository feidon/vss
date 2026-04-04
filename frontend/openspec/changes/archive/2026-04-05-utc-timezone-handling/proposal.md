## Why

All time handling in the frontend relies on implicit JavaScript `Date` behavior — `getHours()`, `toLocaleTimeString()`, and `new Date(localString)` — without any explicit UTC conversion. While epoch timestamps are inherently UTC, the conversions between user input, epoch, and display are implicit and scattered across components. This makes timezone behavior fragile, untestable, and confusing to maintain. The `datetime-local` input interprets values as browser-local time, and display methods use local timezone silently — there is no single source of truth for how time flows through the system.

## What Changes

- Introduce a `TimeUtils` utility with explicit functions: local datetime string to UTC epoch (for API requests), and UTC epoch to local display string (for rendering)
- Update `EpochTimePipe` to use explicit UTC-to-local conversion via `TimeUtils`
- Replace inline `formatTime()` methods in `RouteEditorComponent` and `ConflictAlertComponent` with the shared `TimeUtils` / `EpochTimePipe`
- Update `RouteEditorComponent.onSubmit()` to use `TimeUtils` for converting `datetime-local` input to UTC epoch
- Update `RouteEditorComponent` epoch-to-local reconstruction (for pre-filling the input) to use `TimeUtils`

## Non-goals

- No timezone selector UI — always use the browser's local timezone
- No date library dependency (moment.js, luxon, date-fns) — native `Date` + `Intl` suffice
- No backend changes — the backend already works with UTC epoch seconds
- No changes to `dwell_time` — it's a duration in seconds, not a point in time

## Capabilities

### New Capabilities

- `time-utils`: Centralized timezone conversion utility — local-to-UTC-epoch for API requests, UTC-epoch-to-local for display, replacing scattered inline conversions

### Modified Capabilities

_(none — no existing specs are changing at the requirement level)_

## Impact

- **Components**: `RouteEditorComponent`, `ConflictAlertComponent`, `ScheduleListComponent`, `TimetableDetailComponent` (all use time display)
- **Pipes**: `EpochTimePipe` — internal implementation changes, same public API
- **Services**: No service interface changes — `ServiceService` payloads remain epoch seconds
- **Tests**: `EpochTimePipe` tests need updating to account for explicit timezone handling; new unit tests for `TimeUtils`

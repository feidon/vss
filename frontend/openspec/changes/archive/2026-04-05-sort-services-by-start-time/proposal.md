## Why

The schedule list page displays services in the order returned by the backend (insertion order), making it hard to see the chronological sequence of operations. Sorting by start time gives dispatchers an immediate view of the day's schedule progression.

## What Changes

- Sort the service list in `ScheduleListComponent` by `start_time` ascending
- Services without a start time (null) appear at the end of the list

## Non-goals

- No backend API changes — sorting is client-side only
- No user-selectable sort column or sort direction toggle
- No persistence of sort preference

## Capabilities

### New Capabilities

- `service-list-sorting`: Client-side sorting of the service list by start time in `ScheduleListComponent`

### Modified Capabilities

_(none)_

## Impact

- `ScheduleListComponent` (`src/app/features/schedule/schedule-list.ts`) — add a computed signal that sorts `services()` before rendering
- Existing tests in `schedule-list.spec.ts` may need updated assertions for expected order

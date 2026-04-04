## Why

The schedule list page (`/schedule`) displays origin and destination columns for each service, but they don't show the correct values. The backend API (`GET /api/services`) returns `origin` and `destination` as string names, so the issue is in the frontend rendering or data binding.

## What Changes

- Investigate and fix the `ScheduleListComponent` so that origin and destination columns correctly display the string values returned by the API
- Update the unit test if the existing assertions don't cover the fix scenario

## Non-goals

- No changes to the backend API — the response is confirmed correct
- No changes to other columns or schedule list functionality
- No changes to the `ServiceResponse` model unless the field names don't match the API

## Capabilities

### New Capabilities

_None — this is a bug fix._

### Modified Capabilities

- `service-list`: The origin and destination display requirement is not being met; fix the rendering to match the spec

## Impact

- **Component**: `ScheduleListComponent` (`src/app/features/schedule/schedule-list.ts`)
- **Model** (if needed): `ServiceResponse` (`src/app/shared/models/service.ts`)
- **Test**: `schedule-list.spec.ts` — verify origin/destination assertions

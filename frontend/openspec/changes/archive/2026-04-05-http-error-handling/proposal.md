## Why

The frontend only handles HTTP 409 (conflict) responses from the backend. All other error statuses — including 422 (validation errors with meaningful messages), 4xx, and 5xx — fall through to hardcoded generic messages like "Failed to update route" that hide actionable backend feedback from the user. Additionally, some components (schedule list delete, detail fetch) have no error handling at all, and the error/warning dismiss UX is inconsistent: the schedule editor has a "Dismiss" text button, the conflict alert has an `×` close icon, and block-config errors have no dismiss mechanism.

## What Changes

- Parse and display backend error messages from 422 responses (and other 4xx with `detail` bodies) instead of generic fallback text
- Show a fixed "Something went wrong" message for 500+ server errors
- Add error handling to schedule-list operations (delete, detail fetch, service load) and create-service-dialog submit
- Standardize all dismissible error/warning alerts to use a consistent pattern: same close icon style (`×` button) and same visual treatment (red bordered alert box with close button in top-right)

## Non-goals

- Global HTTP error interceptor — errors will remain component-scoped since different components need different recovery behavior
- Retry mechanisms or toast/snackbar notification systems
- Error logging/reporting infrastructure

## Capabilities

### New Capabilities
- `error-alert`: A shared, reusable error alert component with consistent dismiss UX (× close button, red bordered box), replacing the ad-hoc inline error markup scattered across components

### Modified Capabilities
- `conflict-display`: Conflict alert dismiss button style will be unified with the new error-alert pattern (currently uses `×` icon which becomes the standard; no requirement change, just consistency confirmation)

## Impact

- **Components affected**: `ScheduleEditorComponent`, `ScheduleListComponent`, `CreateServiceDialogComponent`, `BlockConfigComponent`, `ConflictAlertComponent`
- **New file**: `src/app/shared/components/error-alert.ts` (shared alert component)
- **No API changes** — this is purely frontend error handling and UI consistency

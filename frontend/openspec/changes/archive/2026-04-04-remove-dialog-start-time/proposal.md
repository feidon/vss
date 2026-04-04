## Why

The "Create Service" dialog currently collects start time alongside name and vehicle. However, the start time is not sent to `POST /api/services` (which only accepts name + vehicle_id) — it's passed through the dialog result but never consumed by the schedule list. The route editor already has its own start time input. Collecting start time in the dialog is redundant and adds friction to service creation.

## What Changes

- Remove the start time input field from `CreateServiceDialogComponent`
- Remove `startTime` from `CreateServiceDialogResult` interface
- Simplify dialog validation to only require name and vehicle
- Update dialog tests to reflect the simpler form

## Non-goals

- No changes to the route editor's start time handling
- No changes to the `POST /api/services` request

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `create-service-dialog`: Remove start time field; dialog only collects name and vehicle

## Impact

- **Components**: `CreateServiceDialogComponent` — template and logic simplified
- **Interfaces**: `CreateServiceDialogResult` — `startTime` field removed
- **Tests**: `create-service-dialog.spec.ts` — updated for 2-field form

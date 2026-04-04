## Context

The `CreateServiceDialogComponent` has three form fields: name, vehicle, and start time. The start time value is returned via `CreateServiceDialogResult.startTime` but the consumer (`ScheduleListComponent.onCreateService`) only uses `serviceId` for navigation. The route editor (`RouteEditorComponent`) already provides its own start time input, making the dialog's start time field redundant.

## Goals / Non-Goals

**Goals:**
- Remove the start time input from the create-service dialog
- Simplify `CreateServiceDialogResult` to only contain `serviceId`

**Non-Goals:**
- No changes to the route editor or how start time is handled during route editing

## Decisions

### 1. Remove field and simplify interface

**Choice:** Remove the `startTimeLocal` signal, the datetime-local input, its validation, and the `startTime` property from `CreateServiceDialogResult`. The dialog result becomes `{ serviceId: number }`.

**Why:** The start time was never consumed downstream. Removing it simplifies the dialog and the interface without any behavioral change to the application.

## Risks / Trade-offs

None — this is a pure simplification with no functional impact.

## Why

Two bugs degrade the schedule management experience:

1. **Conflict response parsing is broken** — When saving a route triggers a 409 conflict, the error handler looks for conflict data at `err.error.detail.context` but the backend returns it directly at `err.error.detail`. Users see a generic "unexpected format" message instead of the detailed conflict breakdown.
2. **Auto-schedule button has wrong label** — The button reads "Auto Schedule" but should say "Auto-Generate Schedule" to accurately describe its function (triggering backend schedule generation).

## What Changes

- Fix the 409 conflict response extraction path in `ScheduleEditorComponent.saveRoute()` to read from `err.error.detail` instead of `err.error.detail.context`
- Rename the auto-schedule button label from "Auto Schedule" to "Auto-Generate Schedule" in `ScheduleListComponent`

## Non-goals

- No changes to the backend API response format
- No changes to `ConflictResponse` model or conflict display UI
- No changes to `AutoScheduleDialogComponent` behavior

## Capabilities

### New Capabilities

_(none — this is a bugfix change)_

### Modified Capabilities

_(no spec-level requirement changes — these are implementation bugs against existing requirements)_

## Impact

- **`schedule-editor.ts`** — `saveRoute()` error handler (lines 150–157): fix property access path
- **`schedule-list.ts`** — button label text (line 38): rename to "Auto-Generate Schedule"
- No API, dependency, or architectural changes

## Context

The `ScheduleEditorComponent.saveRoute()` method handles 409 conflict responses from `PATCH /api/services/{id}/route`. The backend returns conflict data directly in `err.error.detail` (with fields `vehicle_conflicts`, `block_conflicts`, `interlocking_conflicts`, `battery_conflicts`), but the current code incorrectly looks for it at `err.error.detail.context`.

Separately, the auto-schedule button in `ScheduleListComponent` displays "Auto Schedule" but should read "Auto-Generate Schedule" to match its actual function.

## Goals / Non-Goals

**Goals:**
- Fix conflict response extraction so users see detailed conflict information on 409
- Correct the auto-schedule button label

**Non-Goals:**
- Changing the `ConflictResponse` interface or conflict display UI
- Modifying backend API response format
- Adding new error handling patterns or interceptors

## Decisions

### 1. Fix property access path directly

Change `err.error?.detail?.context` to `err.error?.detail` in `schedule-editor.ts`.

**Rationale:** The `ConflictResponse` type already matches the `detail` object shape. The `.context` intermediate access was simply wrong — the backend never wraps conflicts in a `context` property.

**Alternative considered:** Adding a utility function to normalize various conflict response shapes. Rejected — there is only one shape; the code was just accessing the wrong path.

### 2. Update button label in-place

Change the text content from "Auto Schedule" to "Auto-Generate Schedule" in the template.

**Rationale:** Single string change, no abstraction needed.

## Risks / Trade-offs

- **Low risk**: Both changes are isolated — one property path fix, one label string change. No architectural impact.
- **Verification**: Should be tested manually against the backend to confirm the conflict detail object shape matches `ConflictResponse`.

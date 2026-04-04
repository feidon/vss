## Context

The schedule editor (`features/schedule/`) has two components involved:
- **`RouteEditorComponent`** (route-editor.ts) — manages the stop queue, dwell times, start time, and emits route update requests
- **`ScheduleEditorComponent`** (schedule-editor.ts) — orchestrates the editor page, handles API calls, and displays conflict alerts

Both bugs are in the interaction between these components and the API layer. The code paths exist but don't work correctly.

### Bug 1: Initial state not loading

`RouteEditorComponent.deriveInitialState()` (line 202) is called from an `effect()` in the constructor. The method correctly:
- Filters `route` for non-block nodes
- Computes dwell times from timetable entries
- Extracts start time from first timetable entry

**Likely root cause**: The Angular `effect()` scheduling or the `initialized` guard flag may prevent the method from running when the input signal values change. Needs debugging — the logic is correct but the trigger mechanism may not fire reliably with `input.required()` signals.

### Bug 2: Conflict messages not displaying

`ScheduleEditorComponent.onRouteSubmitted()` (line 75) handles the 409 error:
```typescript
error: (err) => {
  if (err.status === 409) {
    this.conflicts.set(err.error.detail as ConflictResponse);
  }
}
```

**Likely root cause**: The error response shape may not match. The backend returns `{ "detail": { "message": "...", "vehicle_conflicts": [...], ... } }` but `err.error` in Angular's HttpClient is the parsed response body, so `err.error.detail` should be correct. Need to verify the actual response shape at runtime and whether the `ConflictResponse` interface matches (it includes `message` field which aligns).

## Goals / Non-Goals

**Goals:**
- Fix initial state population so editing an existing service shows its current stops, dwell times, and start time
- Fix conflict alert display so 409 responses render the `ConflictAlertComponent` with conflict details

**Non-Goals:**
- No changes to the conflict alert UI design
- No changes to the route update API contract
- No backend changes
- No new components or services

## Decisions

### 1. Debug-first approach over rewrite

**Decision**: Investigate the exact failure points in the existing code before rewriting.

**Rationale**: The logic in `deriveInitialState()` and the conflict handling is structurally correct. The bugs are likely in signal timing, error response parsing, or a mismatch between API shape and TypeScript interface. A targeted fix is less risky than restructuring.

**Alternative**: Rewrite the effect-based initialization as an `ngOnInit` lifecycle hook — only if the effect approach proves fundamentally incompatible with `input.required()` signals.

### 2. Runtime verification of API error shape

**Decision**: Add `console.log` or breakpoint to verify the actual 409 response structure before assuming the parsing path is correct.

**Rationale**: The backend 409 response nesting (`detail.message`, `detail.vehicle_conflicts`, etc.) must exactly match what the frontend reads from `err.error.detail`. A single level of nesting mismatch silently produces `undefined`.

## Risks / Trade-offs

- **[Signal timing]** → If `effect()` doesn't reliably fire for `input.required()` in Angular 21, fall back to `ngOnChanges` or explicit initialization in a lifecycle hook.
- **[Error shape mismatch]** → If the API changed its error envelope, the `ConflictResponse` interface and the error parsing path both need updating. Low risk since the interface already includes `message` field matching the API.

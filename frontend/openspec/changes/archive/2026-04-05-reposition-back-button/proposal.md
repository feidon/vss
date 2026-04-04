## Why

The "← Back to Schedule" button currently sits inline with the service name (e.g., "s1") in a flex row, making the header area feel cluttered. The button competes visually with the page title and pushes content down unnecessarily. Moving it to a less prominent position improves the visual hierarchy of the schedule editor.

## What Changes

- Restyle the "Back to Schedule" navigation in `ScheduleEditorComponent` — change it from a prominent inline button to a subtle text link positioned above the service title
- The service name heading gets more visual prominence as the primary page element

## Non-goals

- Changing the route or navigation behavior (still links to `/schedule`)
- Modifying any other component layout
- Adding breadcrumb navigation

## Capabilities

### New Capabilities

- `back-nav-style`: Reposition and restyle the back navigation link in the schedule editor header

### Modified Capabilities

_(none)_

## Impact

- **Code**: `src/app/features/schedule/schedule-editor.ts` — template changes only (HTML + Tailwind classes)
- **APIs**: None
- **Dependencies**: None

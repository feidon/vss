## Why

When a user requests an auto-generated schedule with an interval that is too short for the track's interlocking constraints, the backend raises `INTERVAL_BELOW_MINIMUM` with rich context (`requested_interval`, `minimum_interval`, `dwell_time`, `min_departure_gap`). However, the frontend has no formatter for this error code, so the user sees only a generic "Failed to generate schedule." message — losing the actionable detail about what minimum interval would work.

## What Changes

- **Frontend**: Add an `INTERVAL_BELOW_MINIMUM` entry to `ERROR_FORMATTERS` in `error-utils.ts` that renders a user-friendly message using the context fields (requested interval, minimum achievable interval).
- **Frontend**: Add unit tests for the new formatter.

## Capabilities

### New Capabilities
- `interval-below-minimum-error`: Frontend error formatting for the `INTERVAL_BELOW_MINIMUM` error code, displaying the requested interval and the minimum achievable interval to the user.

### Modified Capabilities

_(none — the backend already raises this error with the correct code and context; no spec-level requirement changes)_

## Impact

- **Frontend `error-utils.ts`**: New formatter entry added to `ERROR_FORMATTERS`.
- **Frontend `error-utils.spec.ts`**: New test cases for the formatter.
- **Auto-schedule dialog**: No code changes — it already calls `extractErrorMessage`, so the new formatter is picked up automatically.
- **Backend**: No changes needed — `INTERVAL_BELOW_MINIMUM` error code and context are already in place.

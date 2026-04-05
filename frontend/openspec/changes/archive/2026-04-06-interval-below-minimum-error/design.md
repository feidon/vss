## Context

The backend already raises `DomainError(ErrorCode.INTERVAL_BELOW_MINIMUM, ...)` with a context dict containing `requested_interval`, `minimum_interval`, `dwell_time`, and `min_departure_gap` when the user's requested schedule interval is too short for the track's interlocking constraints.

The frontend's `extractErrorMessage()` in `error-utils.ts` looks up `ERROR_FORMATTERS[error_code]` to produce user-friendly messages. There is currently no entry for `INTERVAL_BELOW_MINIMUM`, so the auto-schedule dialog falls through to the generic "Failed to generate schedule." fallback.

## Goals / Non-Goals

**Goals:**
- Display a clear, actionable error message when `INTERVAL_BELOW_MINIMUM` is returned, telling the user their requested interval and the minimum achievable interval.
- Maintain consistency with the existing `ERROR_FORMATTERS` pattern.

**Non-Goals:**
- Modifying the backend error code, context fields, or HTTP status.
- Changing the auto-schedule dialog's error handling flow (it already uses `extractErrorMessage`).
- Adding UI affordances like auto-correcting the interval input field.

## Decisions

**1. Formatter uses `requested_interval` and `minimum_interval` context fields**

The formatter reads numeric values from the error context and renders a message like:
`"Interval 59s is below the minimum of 60s due to interlocking constraints."`

This keeps the message concise and actionable — the user knows exactly what value to increase to.

Alternative considered: Including `dwell_time` and `min_departure_gap` in the message. Rejected because these are internal solver details that would confuse most users.

**2. Fallback to `null` when context fields are missing**

Consistent with existing formatters (e.g., `INSUFFICIENT_VEHICLES`), the formatter returns `null` if the expected numeric fields are absent, letting `extractErrorMessage` fall through to the generic fallback. This keeps the formatter defensive.

## Risks / Trade-offs

- **[Low]** If backend changes the context field names → formatter returns `null` and user sees generic fallback. Acceptable degradation. Mitigation: unit test asserts on specific context shape.

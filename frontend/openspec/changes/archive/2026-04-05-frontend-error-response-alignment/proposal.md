## Why

The backend has removed the `message` field from all error responses, now returning only `{ "detail": { "error_code": "...", "context": {...} } }`. The frontend's `ErrorDetail` interface still declares `message: string`, and `extractErrorMessage` has fallback paths that rely on `detail.message` — these paths are now dead code that will silently return `undefined` instead of the intended fallback string.

## What Changes

- **BREAKING**: Remove `message` field from `ErrorDetail` interface to match the backend schema
- Remove fallback-to-`detail.message` paths in `extractErrorMessage` (lines 92, 95-96) — when a formatter returns `null` or the error code is unknown, fall through to the `fallback` parameter instead
- Update unit tests that include `message` in mock error payloads to reflect the actual backend response shape
- Update the `structured-error-display` spec to remove scenarios referencing `detail.message`

## Non-goals

- No changes to `ERROR_FORMATTERS` logic or the `buildNameMap` utility
- No changes to component-level error handling code (components already pass `nameMap` and `fallback` correctly)
- No new error codes or formatters

## Capabilities

### New Capabilities

_(none)_

### Modified Capabilities

- `structured-error-display`: Remove `message` from `ErrorDetail` interface; remove `detail.message` fallback behavior from `extractErrorMessage`
- `error-alert`: Update scenario for "object detail containing message" since backend no longer sends `message`

## Impact

- `src/app/shared/models/error.ts` — remove `message` field
- `src/app/shared/utils/error-utils.ts` — remove `detail.message` fallback branches
- `src/app/shared/utils/error-utils.spec.ts` — remove `message` from test payloads, update expectations for fallback scenarios
- `openspec/specs/structured-error-display/spec.md` — remove `message` references from scenarios
- `openspec/specs/error-alert/spec.md` — update "object detail containing message" scenario

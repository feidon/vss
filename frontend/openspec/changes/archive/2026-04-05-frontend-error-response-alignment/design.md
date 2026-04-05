## Context

The backend unified its error responses to `{ "detail": { "error_code": string, "context": dict } }`, removing the `message` field entirely. The frontend already has `ERROR_FORMATTERS` that generate user-facing messages from `error_code` + `context`, but retains dead fallback paths that read `detail.message`. The `ErrorDetail` interface also still declares `message: string`.

## Goals / Non-Goals

**Goals:**
- Align `ErrorDetail` interface with the actual backend schema
- Remove dead `detail.message` fallback paths so unknown/unformattable errors fall through to the caller-provided `fallback` string
- Keep tests honest by removing `message` from mock payloads

**Non-Goals:**
- Changing formatter logic or adding new error codes
- Modifying component-level error handling (components already supply `fallback` and `nameMap`)
- Handling 409 conflict responses (separate code path, unaffected)

## Decisions

### 1. Remove `message` from `ErrorDetail` — not make it optional

**Choice**: Delete the field entirely rather than `message?: string`.

**Rationale**: The backend no longer sends it. Making it optional preserves a lie in the type system — consumers might still write code expecting it. Removing it makes the type honest and lets the compiler catch any remaining references.

**Alternative considered**: `message?: string` for "backward compatibility" — rejected because there is no backward to be compatible with; the backend change is already deployed.

### 2. Fallback chain: formatter → fallback parameter (remove `detail.message` step)

**Current chain**: formatter → `detail.message` → `fallback`
**New chain**: formatter → `fallback`

When a formatter returns `null` (e.g., UUID not in name map) or the error code has no formatter, `extractErrorMessage` will return the caller's `fallback` string directly.

**Rationale**: The `detail.message` step is dead code — backend never sends it. Keeping it would mask bugs where a formatter incorrectly returns `null`.

### 3. Remove the standalone `detail.message` object check (lines 95-96)

The second branch `if (detail && typeof detail === 'object' && typeof detail.message === 'string')` handled responses with `message` but no `error_code`. Since the backend now always sends `error_code`, this branch is unreachable. Remove it.

## Risks / Trade-offs

- **[Risk] Future error codes without formatters return generic fallback** → This is the correct behavior. The fallback is descriptive (e.g., "Failed to update route"). If richer messages are needed later, add a formatter.
- **[Risk] Tests that relied on `detail.message` fallback will need updated expectations** → Two tests change: "UUID not in name map" and "unknown error code" now expect `fallback` instead of `message`.

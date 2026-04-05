## Context

The backend now returns structured error responses for all non-409 errors:

```json
{ "detail": { "error_code": "STOP_NOT_FOUND", "message": "Stop ... not found", "context": { "stop_id": "uuid" } } }
```

409 conflicts retain their existing structure (with `vehicle_conflicts`, `block_conflicts`, etc.) — this already works in the frontend.

Currently, `extractErrorMessage()` in `error-utils.ts` extracts `detail.message` as a plain string. The `context` field (containing UUIDs for vehicles, blocks, stops, nodes) is discarded. Users see backend messages with raw UUIDs instead of human-readable names like "P1A" or "V1".

Each component that handles errors already has access to domain data that can resolve UUIDs:
- **ScheduleEditorComponent**: has `service().graph` (nodes, edges, vehicles)
- **CreateServiceDialogComponent**: has `vehicles()` list
- **BlockConfigComponent**: has `blocks()` list
- **ScheduleListComponent**: has `services()` list and `detailCache()`

## Goals / Non-Goals

**Goals:**
- Parse the new `ErrorDetail` structure (`error_code`, `message`, `context`) into user-friendly messages
- Replace raw UUIDs in error messages with human-readable names (e.g., "P1A", "V1", "B3")
- Keep error handling per-component (no global interceptor)
- Maintain backward compatibility if backend returns the old string format during rollout

**Non-Goals:**
- Adding a centralized error service or HTTP interceptor
- Making additional API calls to resolve UUIDs
- Changing the 409 conflict alert component (already works with name mapping)
- Handling error codes that the frontend never triggers

## Decisions

### 1. Name resolver as a pure function taking a `Map<string, string>`

Each component builds a `Map<string, string>` (UUID → name) from its already-loaded domain data, then passes it to the error formatting function. This avoids a shared service that would need injection and state synchronization.

**Alternative considered**: A singleton `NameResolverService` that caches all known entities. Rejected because it adds coupling — components would need to pre-populate the cache, and cache staleness would be a concern. The map-per-call approach is simpler and stateless.

### 2. Extend `extractErrorMessage` with an optional name map parameter

The function signature becomes:
```typescript
extractErrorMessage(error: HttpErrorResponse, fallback: string, nameMap?: ReadonlyMap<string, string>): string
```

When `nameMap` is provided and the error has a `context` with UUID fields, those UUIDs are replaced with names from the map. This is backward-compatible — existing call sites without a name map continue to work unchanged.

**Alternative considered**: A separate `formatStructuredError()` function. Rejected because it would require every call site to first check whether the error is structured, creating duplicated branching logic. Extending the existing function keeps the API surface small.

### 3. Add an `ErrorDetail` interface in shared models

```typescript
interface ErrorDetail {
  readonly error_code: string;
  readonly message: string;
  readonly context: Readonly<Record<string, unknown>>;
}
```

This types the `detail` field of non-409 error responses. The `error_code` string is not turned into a TypeScript enum because we don't want the frontend to break when the backend adds new error codes.

### 4. Format strategy: message with name substitution, not code-based message templates

Rather than maintaining a frontend mapping of `error_code → template string`, we use the backend's `message` field (which is already human-readable) and substitute any UUID values found in `context` with their mapped names.

The substitution scans `context` values: if a value is a string that exists as a key in `nameMap`, it gets replaced in the message text. This is generic and doesn't require updating the frontend when new error codes are added.

**Alternative considered**: A `switch` on `error_code` with custom message templates per code. Rejected because it duplicates the backend's message authoring and requires frontend changes for every new error code.

### 5. Components build name maps from local data

| Component | Data source | Map contents |
|-----------|------------|--------------|
| ScheduleEditorComponent | `service().graph` | nodes, edges, vehicles |
| CreateServiceDialogComponent | `vehicles()` | vehicles |
| BlockConfigComponent | `blocks()` | blocks |
| ScheduleListComponent | none (generic messages sufficient) | empty or omitted |

The name map is built at error-handling time, not precomputed, since signals are already reactive and the overhead is negligible for error paths.

## Risks / Trade-offs

- **Backend message contains UUID literal** → If the backend message says "Vehicle abc-123 not found" and we have a mapping for `abc-123` → `V1`, the substitution replaces it to "Vehicle V1 not found". This works because backend messages embed the same UUIDs as the context values. **Risk**: If the backend changes message format to not include the UUID, substitution silently does nothing and the original message is shown — acceptable degradation.

- **Unknown UUID in context** → If a UUID isn't in the name map, it stays as-is in the message. This matches the existing `ConflictAlertComponent` fallback behavior. **Mitigation**: The backend message is still meaningful without the substitution.

- **New error codes** → No frontend change needed. The generic substitution approach handles any error code. Only if we want code-specific UI behavior (e.g., highlighting a specific field) would we need to handle a new code explicitly.

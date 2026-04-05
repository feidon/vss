## Why

The backend has migrated from flat string error responses (`{"detail": "message"}`) to structured error responses with `error_code`, `message`, and `context` fields. The frontend's `extractErrorMessage` utility only reads the message string, discarding the error code and context. Users see generic messages like "Failed to update route" when the backend now provides enough detail to say "Stop P2A not found" or "No route between P1A and P3B". UUIDs in the context need to be resolved to human-readable names before display.

## What Changes

- **BREAKING**: Update `extractErrorMessage` to parse the new structured `ErrorDetail` format (`{ error_code, message, context }`) and produce user-friendly messages that incorporate context fields
- Add an `ErrorDetail` TypeScript interface matching the backend schema and an error-code-to-message mapping that resolves context UUIDs to names
- Update `ConflictAlertComponent` and `ScheduleEditorComponent` to handle the structured 409 format consistently (no behavior change needed — 409 already works, just ensure `error_code` presence doesn't break parsing)
- Update `CreateServiceDialogComponent` and `BlockConfigComponent` to display richer error messages from structured responses
- Add a shared name-resolver utility that maps UUIDs to names using already-loaded data (graph nodes/edges, vehicles, blocks) so no additional API calls are needed

## Non-goals

- Adding a global HTTP error interceptor — error handling remains per-component
- Adding new API calls solely for UUID resolution — use data already available in components
- Changing the 409 conflict alert UI — it already handles conflicts well with name mapping
- Handling backend errors that the frontend never encounters (e.g., schedule generation errors)

## Capabilities

### New Capabilities

- `structured-error-display`: Parse backend structured error responses (`ErrorDetail` with `error_code`, `message`, `context`) and render user-friendly messages with UUID-to-name resolution

### Modified Capabilities

- `error-alert`: Update the existing error alert flow to consume structured error details instead of plain strings

## Impact

- **Models**: New `ErrorDetail` interface in `shared/models/`
- **Utils**: `error-utils.ts` updated to parse structured responses and resolve names from context
- **Components**: `schedule-editor.ts`, `schedule-list.ts`, `create-service-dialog.ts`, `block-config.ts` — updated error handlers to pass name-resolution context
- **No new API calls**: Name resolution uses data already loaded by each component (graph, blocks, vehicles)

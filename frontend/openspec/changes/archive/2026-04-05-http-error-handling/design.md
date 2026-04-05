## Context

The frontend currently handles only HTTP 409 (conflict) responses in the schedule editor. All other HTTP errors either show hardcoded generic messages or are silently swallowed. The backend sends structured error details on 422 (validation) and other 4xx statuses via a `detail` field, but the frontend never reads them.

Additionally, error dismissal is inconsistent across the app:
- **ConflictAlertComponent**: `×` icon button in top-right corner, emits `dismiss` output
- **ScheduleEditorComponent** error message: "Dismiss" text button on the right side of the alert
- **BlockConfigComponent**: plain red text `<p>` with no dismiss mechanism
- **CreateServiceDialogComponent**: plain red text `<p>` with no dismiss mechanism

## Goals / Non-Goals

**Goals:**
- Extract a shared `ErrorAlertComponent` with a consistent dismiss UX (`×` close button, same visual treatment as conflict alert)
- Extract a helper function to parse backend error messages from HTTP error responses across status codes (422 detail messages, other 4xx, 500+ fallback)
- Add error handling to all unhandled HTTP operations (schedule-list delete/fetch, create-service-dialog submit)
- Replace all inline error markup with the shared component

**Non-Goals:**
- Global HTTP interceptor (component-scoped handling preserved for different recovery behaviors)
- Retry/toast/snackbar systems
- Error reporting infrastructure

## Decisions

### Decision 1: Shared presentational `ErrorAlertComponent` over duplicated inline markup

Create `src/app/shared/components/error-alert.ts` as a dumb presentational component with `message` input and `dismiss` output. All components use this instead of their own inline error divs.

**Rationale**: The conflict alert already established the visual pattern (red bordered box, `×` button top-right). Extracting a shared component ensures consistency and avoids the current drift where each component invents its own error display.

**Alternative considered**: A global notification/toast service. Rejected because errors need to appear in-context (near the action that failed) and different components have different recovery behaviors. A toast would lose spatial context.

### Decision 2: Helper function for error message extraction

Create a `extractErrorMessage(error: HttpErrorResponse, fallback: string): string` utility in `src/app/shared/utils/error-utils.ts`. Logic:
1. If `status >= 500` → return `'Something went wrong. Please try again later.'` (constant)
2. If `error.error?.detail` is a string → return it
3. If `error.error?.detail?.message` is a string → return it (structured error with message field)
4. Otherwise → return the provided `fallback` string

**Rationale**: The backend's error response format uses `detail` (FastAPI convention). Centralizing extraction avoids each component reimplementing the same parsing. The fallback parameter lets each call site control the generic message for truly unexpected errors.

**Alternative considered**: Parsing in an HTTP interceptor. Rejected because the interceptor would need to re-throw a modified error, adding complexity. A simple utility function is easier to test and understand.

### Decision 3: Keep 409 handling as-is in schedule editor

The existing `ConflictAlertComponent` with its dedicated conflict response parsing remains untouched. The `×` dismiss icon pattern it uses becomes the standard. Only the schedule editor's generic `errorMessage` display (the "Dismiss" text button) gets replaced with the shared `ErrorAlertComponent`.

**Rationale**: 409 responses have a rich structured format that requires a specialized display component. Unifying the dismiss icon style is sufficient.

### Decision 4: Component-scoped error handling, no interceptor

Each component handles its own errors locally via subscribe error callbacks, using `extractErrorMessage` + `ErrorAlertComponent`.

**Rationale**: Different components need different recovery behaviors:
- Schedule editor: shows error near the route form
- Block config: shows error near the table, rolls back optimistic update
- Create service dialog: shows error inside the dialog, resets saving state
- Schedule list: shows error at the top of the list

## Risks / Trade-offs

- **[Risk] Backend error format changes** → The `extractErrorMessage` function handles multiple formats (string detail, object detail with message, null). If the backend adds a new format, only the utility function needs updating.
- **[Trade-off] No global error boundary** → Unhandled errors in components without explicit subscribe error handlers will still fail silently. Accepted because adding handlers to all remaining operations is part of this change's scope.
- **[Trade-off] Two alert components** → `ConflictAlertComponent` (rich conflict display) and `ErrorAlertComponent` (simple message) coexist. This is intentional — they serve different purposes, but share the same visual dismiss pattern.

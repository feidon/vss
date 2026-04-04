## Context

The schedule list page (`ScheduleListComponent`) displays a table of services with origin and destination columns. The `ServiceResponse` interface already defines `origin: string | null` and `destination: string | null`, and the template binds them via `{{ service.origin ?? '—' }}`. The backend `GET /api/services` returns these fields as string names (e.g., "P1A", "P2A").

Despite this, the columns don't show the correct values at runtime. The root cause needs to be identified — possible causes include:
1. API response field name mismatch (e.g., snake_case vs camelCase)
2. Angular HttpClient not mapping the fields correctly
3. The API response shape differing from the `ServiceResponse` interface

## Goals / Non-Goals

**Goals:**
- Identify and fix the root cause of origin/destination not displaying correctly
- Ensure both columns render the string names from the API response
- Maintain existing null-handling (show "—" when origin/destination is null)

**Non-Goals:**
- Changing the backend API response format
- Adding new columns or functionality to the schedule list
- Refactoring the component architecture

## Decisions

**Decision 1: Debug-first approach**
Investigate the actual API response at runtime to identify the field name mismatch or binding issue, then apply the minimal fix. No speculative changes.

*Rationale*: The TypeScript interface and template look correct on paper. The bug is likely a subtle mismatch between the actual API response shape and the interface definition. Fixing based on the actual response avoids introducing new issues.

**Decision 2: Fix at the model or template layer only**
The fix should be confined to either the `ServiceResponse` interface (if field names are wrong) or the template binding (if the data path is wrong). No new services or pipes needed.

*Rationale*: This is a display bug, not an architectural issue.

## Risks / Trade-offs

- **[Risk] Fix may require verifying actual API response shape** → Run the dev server and inspect the network response, or check the backend API serialization to confirm field names.
- **[Risk] Other components may reference the same interface** → Search for `ServiceResponse` usage before renaming any fields.

## Context

The schedule list page (`ScheduleListComponent`) displays services in backend insertion order. The `ServiceResponse` model already includes a `start_time: number | null` field. The template iterates `services()` directly — there is no intermediate sorted signal.

## Goals / Non-Goals

**Goals:**
- Sort the service list by `start_time` ascending so dispatchers see chronological order
- Place services with no start time (null) at the end

**Non-Goals:**
- No backend changes — sorting is purely client-side
- No sortable column headers or user-configurable sort direction
- No secondary sort key beyond start_time (ties keep original order)

## Decisions

### 1. Use a `computed()` signal for sorted list

**Decision**: Add a `sortedServices = computed(...)` signal that derives from `services()` and sort by `start_time` ascending. The template iterates `sortedServices()` instead of `services()`.

**Rationale**: This follows the existing signal-based reactive pattern in the codebase. `computed()` automatically re-evaluates when `services()` changes, with no manual subscription management. The sort is derived state — exactly what `computed()` is designed for.

**Alternative considered**: Sorting inside `loadServices()` before setting the signal. Rejected because it mixes data fetching with presentation concerns and wouldn't re-sort if services were ever updated from another source.

### 2. Null start_time sorts last

**Decision**: Services with `start_time === null` sort after all services with a numeric start time.

**Rationale**: Null start time means the service has no route/timetable yet — it's incomplete and less operationally relevant. Placing it last keeps the focus on scheduled services.

## Risks / Trade-offs

- **[Performance]** Sorting on every signal read is O(n log n). With the expected service count (<100), this is negligible. → No mitigation needed.
- **[Stability]** JavaScript's `Array.sort` is not guaranteed stable in all engines. For services with the same start_time, relative order may vary. → Acceptable for this use case; no secondary sort key is needed.

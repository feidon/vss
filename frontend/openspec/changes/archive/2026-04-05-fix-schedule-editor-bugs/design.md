## Context

The schedule editor (`ScheduleEditorComponent`) fetches service details from the API and passes them to child components. Two child components have bugs:

1. **`RouteEditorComponent`** (`route-editor.ts`) — Initializes stops in `ngOnInit()` via `deriveInitialState()`. Since `ngOnInit()` runs once per component lifecycle, the stops signal retains stale state (including manually-added stops) when the parent's `service` input changes on refresh.

2. **`ConflictAlertComponent`** (`conflict-alert.ts`) — Builds a `nodeNameMap` from `graph.nodes` only. Block IDs in conflict responses reference `graph.edges`, so they miss the map and fall back to displaying raw UUIDs.

## Goals / Non-Goals

**Goals:**
- Stops queue resets to API-only data whenever the `service` input signal changes
- Block names in conflict alerts resolve from graph edges, not just nodes

**Non-Goals:**
- Refactoring the route editor's overall state management
- Changing the backend API response structure

## Decisions

### 1. Use `effect()` to watch `service` input in RouteEditorComponent

Replace the `ngOnInit()` call to `deriveInitialState()` with an `effect()` in the constructor that watches `this.service()`. This re-derives stops whenever the service input changes (including initial load).

**Rationale:** Angular signals + `effect()` is the idiomatic way to react to input changes in standalone components. Avoids lifecycle timing issues entirely.

### 2. Extend `nodeNameMap` to include graph edges

Add a loop over `this.graph().edges` in the `nodeNameMap` computed signal, mapping each edge's `id` to its `name`.

**Rationale:** Minimal change — one extra `for` loop in the existing computed signal. No new abstractions needed.

## Risks / Trade-offs

- **Effect firing on initial load** — The `effect()` will also fire on first load, replacing the `ngOnInit()` call. This is equivalent behavior since `deriveInitialState()` is called with the same value. No risk.
- **Edge/node ID collisions in name map** — If an edge and node share the same ID, the last-written wins. In practice, the backend uses UUIDs so collisions are impossible. No mitigation needed.

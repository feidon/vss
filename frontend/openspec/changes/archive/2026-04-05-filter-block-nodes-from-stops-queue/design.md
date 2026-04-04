## Context

`RouteEditorComponent.deriveInitialState()` (route-editor.ts:157-177) runs when the service input changes. It maps all nodes from `svc.route` into the `stops` signal. The backend returns `svc.route` as the full path including intermediate block nodes (e.g., `[P1A, B3, B5, P2A]`). The stops signal drives both the stop list UI and the `stopsChanged` output which highlights queued nodes on the track map.

The `Node` type is currently `PlatformNode | YardNode` (no BlockNode), but at runtime block nodes arrive with `type: 'block'`. The sibling change `fix-track-map-and-timetable-bugs` adds `BlockNode` to the union, which will make the type guard cleaner. This fix should work regardless — filtering on `node.type !== 'block'` works at runtime even without the type definition.

## Goals / Non-Goals

**Goals:**
- Filter block nodes out of the stops queue when deriving initial state from an existing service route
- Ensure the track map only highlights platform/yard nodes as queued stops

**Non-Goals:**
- Changing `addStopFromMap()` — already only receives platform/yard clicks
- Changing timetable display — blocks should still appear there
- Changing the `Node` type definition (handled by sibling change)

## Decisions

### 1. Filter at `deriveInitialState` source

**Decision**: Add `.filter()` on `svc.route` at line 165 to exclude nodes with `type === 'block'` before mapping to `StopEntry[]`.

**Rationale**: This is the single point where the stops signal is populated from existing route data. Filtering here fixes both the stop list and the map markers (via `stopsChanged`). No other code path needs changing — `addStopFromMap` already only receives platform/yard nodes from the track map click handler.

**Alternative considered**: Filtering in the `stopsChanged` effect — rejected because the stop list table would still show block entries.

## Risks / Trade-offs

- **[Risk] Node type union doesn't include 'block' yet**: The runtime value `node.type === 'block'` is correct even though TypeScript doesn't know about it. Once the sibling change adds `BlockNode`, the filter becomes fully type-safe. No risk at runtime.

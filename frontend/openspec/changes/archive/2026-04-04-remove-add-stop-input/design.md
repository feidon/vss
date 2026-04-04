## Context

The schedule editor provides two methods to add stops to a service route: a dropdown select + "Add" button in `RouteEditorComponent`, and clicking platform/yard nodes on the track map in `TrackMapEditorComponent`. Both feed into the same stop list. The dropdown is redundant since the track map provides a more intuitive spatial interaction, but the map currently lacks clear affordance for new users.

Key components:
- `RouteEditorComponent` (`route-editor.ts`) — owns the stop list, dropdown, dwell time editing, reordering
- `TrackMapEditorComponent` (`track-map-editor.ts`) — d3.js SVG rendering, click handlers, hover tooltips
- `ScheduleEditorComponent` (`schedule-editor.ts`) — parent that wires map clicks to route editor via `addStopFromMap()`

## Goals / Non-Goals

**Goals:**
- Remove the dropdown-based stop addition UI (select + button) from `RouteEditorComponent`
- Add a visible hint near the track map guiding users to click nodes to add stops
- Ensure clickable nodes have clear pointer cursor affordance

**Non-Goals:**
- Changing the track map rendering, click handling, or queue visualization
- Modifying stop queue management (reorder, remove, dwell time editing)
- Adding keyboard-based stop selection or search

## Decisions

### 1. Place hint text above the track map in `TrackMapEditorComponent`

**Decision:** Add a small instructional text line ("Click a platform or yard on the map to add a stop") rendered as HTML above the SVG canvas within `TrackMapEditorComponent`.

**Rationale:** The hint is about the map interaction, so it belongs with the map component. Placing it above the SVG ensures visibility without overlapping the visualization.

**Alternative considered:** Placing the hint in `ScheduleEditorComponent` as a section header — rejected because it couples layout knowledge about the map's interaction model to the parent.

### 2. Conditionally show hint only when stop queue is empty

**Decision:** Show the hint text when no stops have been added yet. Once the user adds their first stop, the hint disappears — they've learned the interaction.

**Rationale:** Avoids permanent visual clutter for experienced users while guiding first-time interaction. The queue indicators (numbered circles on nodes) serve as ongoing visual feedback.

**Alternative considered:** Always showing the hint — rejected as unnecessary noise once the user understands the pattern.

### 3. Remove station-related inputs from `RouteEditorComponent`

**Decision:** Remove `stations`, `yardNodeId()`, `nodeName()`, `selectedNodeId`, and `addStop()` from `RouteEditorComponent`. Keep `addStopFromMap()` as the only entry point for adding stops.

**Rationale:** These exist solely to support the dropdown. The component becomes simpler with a single code path for stop addition (via parent calling `addStopFromMap()`).

### 4. Ensure pointer cursor on clickable nodes

**Decision:** Add `cursor: pointer` styling to platform and yard node groups in the d3.js rendering.

**Rationale:** Standard web affordance — users expect clickable elements to show a pointer cursor. The existing hover highlight helps but cursor change is the primary affordance.

## Risks / Trade-offs

- **Discoverability for new users** → Mitigated by the conditional hint text and pointer cursor. The hint explicitly tells users what to do on their first interaction.
- **Loss of station grouping context** → The dropdown organized stops by station (optgroup). Users lose this grouping, but the map provides spatial context which is arguably more useful. The tooltip on hover shows node names.
- **No keyboard-only stop addition** → Removing the dropdown eliminates the only keyboard-accessible way to add stops. Acceptable for now since the track map is the primary interaction; accessibility improvements can be addressed separately if needed.

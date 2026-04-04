## Why

The schedule editor currently provides two ways to add stops: a dropdown select + "Add" button in the route editor panel, and clicking directly on the track map. The dropdown is redundant — the track map provides a more intuitive spatial interaction. However, the map lacks clear affordance telling users they can click nodes to add stops. Removing the dropdown and adding a visual hint will simplify the UI and guide users toward the primary interaction.

## What Changes

- **Remove** the `<select>` dropdown and "Add" button from `RouteEditorComponent`
- **Remove** the `addStop()` method and `selectedNodeId` signal from `RouteEditorComponent`
- **Remove** station-related inputs (`stations`, `yardNodeId`, `nodeName`) that only served the dropdown
- **Add** a hint/instruction text near the track map (e.g., "Click a platform or yard on the map to add a stop") to guide users toward the click interaction
- **Enhance** cursor styling on clickable nodes (pointer cursor) for better affordance

## Non-goals

- Changing the track map click-to-add-stop behavior itself (already works)
- Modifying the stop queue panel (reorder, remove, dwell time editing stays)
- Adding drag-and-drop or other new interaction patterns

## Capabilities

### New Capabilities

- `map-click-hint`: Visual hint/instruction guiding users to click the track map to add stops

### Modified Capabilities

- `track-map-editor`: Remove dropdown-based stop addition from the stop queue panel requirement; the only way to add stops is via map click

## Impact

- **RouteEditorComponent** (`route-editor.ts`): Remove dropdown HTML, `addStop()`, `selectedNodeId`, and station-related inputs
- **ScheduleEditorComponent** (`schedule-editor.ts`): Remove station data passing to route editor for the dropdown
- **TrackMapEditorComponent** (`track-map-editor.ts`): Add hint text, ensure pointer cursor on clickable nodes
- No API changes — this is purely a frontend UI simplification

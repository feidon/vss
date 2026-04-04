## 1. Remove dropdown UI from RouteEditorComponent

- [x] 1.1 Remove `<select>` dropdown and "Add" button HTML from `route-editor.ts` template
- [x] 1.2 Remove `selectedNodeId` signal, `addStop()` method, and station-related inputs (`stations`, `yardNodeId`, `nodeName`) from `route-editor.ts`
- [x] 1.3 Remove station data passing from `ScheduleEditorComponent` template to `RouteEditorComponent`

## 2. Add map click hint to TrackMapEditorComponent

- [x] 2.1 Add `queuedNodeIds` input (or equivalent) to `TrackMapEditorComponent` so it can determine if the queue is empty
- [x] 2.2 Add conditional hint text ("Click a platform or yard on the map to add a stop") above the SVG, shown only when queue is empty
- [x] 2.3 Add `cursor: pointer` styling to clickable platform/yard node groups in d3.js rendering

## 3. Cleanup and verification

- [x] 3.1 Remove any unused imports, interfaces, or helper methods left over from the dropdown removal
- [x] 3.2 Verify the app compiles cleanly (`ng build`) and lint passes (`ng lint`)
- [x] 3.3 Manual smoke test: add stops via map click, verify hint appears/disappears, verify pointer cursor on clickable nodes

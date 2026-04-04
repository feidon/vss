## 1. Fix Node Type Model

- [x] 1.1 Add `BlockNode` interface to `src/app/shared/models/node.ts` with type `'block'` and include it in the `Node` union type
- [x] 1.2 Update any type guards or switch statements on `node.type` across the codebase to handle the new `'block'` variant

## 2. Fix Timetable Node Name Resolution

- [x] 2.1 Update `RouteEditorComponent.nodeName()` in `route-editor.ts` to search `service().route` first, then `graph().edges`, then fall back to raw ID
- [x] 2.2 Update `RouteEditorComponent.nodeType()` (if used in timetable) to search `service().route` for proper type resolution of block nodes — N/A: route-editor timetable has no type column
- [x] 2.3 Update tests in `route-editor.spec.ts` to verify block node names resolve correctly in the timetable display
- [x] 2.4 Update `TimetableDetailComponent.findNode()` in `timetable-detail.ts` — already searches `service().route` which includes blocks; BlockNode now in Node union makes this work correctly

## 3. Fix Arrowhead Rendering

- [x] 3.1 Increase marker dimensions to `markerWidth=8, markerHeight=8` and change fill to `#64748b` (slate-500) for contrast in `track-map-editor.ts`
- [x] 3.2 Shorten edge line endpoints (x2, y2) by target node radius (12 for nodes, 4 for junctions) so arrowheads render at the circle boundary
- [x] 3.3 Update tests in `track-map-editor.spec.ts` to verify marker dimensions, fill color, and line endpoint shortening

## 4. Fix Edge Label Overlap

- [x] 4.1 Increase base label offset from 10px to 14px in `track-map-editor.ts`
- [x] 4.2 Add index-based staggering: group edges by shared endpoint pair and apply progressive offset multiplier per group index
- [x] 4.3 Update tests in `track-map-editor.spec.ts` to verify label separation accounts for text bounding box width (centers > 15px apart)

## 5. Verify All Fixes

- [x] 5.1 Run full test suite (`ng test`) and fix any regressions
- [x] 5.2 Run lint (`ng lint`) and format check (`npx prettier --check "src/**/*.{ts,html,css}"`)

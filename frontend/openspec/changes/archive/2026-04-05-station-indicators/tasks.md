## 1. Station Bounding Box Computation

- [x] 1.1 In `TrackMapEditorComponent.render()`, after building `posMap` and defining scales, compute bounding boxes for each station: iterate `graph.stations`, look up each `platform_ids` entry in the node list, compute min/max of scaled (x, y), apply 30px padding, enforce 60×60px minimum size
- [x] 1.2 Write tests verifying bounding box computation: multi-platform station encloses both platforms, single-platform station meets minimum size

## 2. Station Rectangle Rendering

- [x] 2.1 After clearing SVG and defining arrowhead marker (before edges), render `g.station` groups for each station: append a `rect` with rounded corners, light fill (#e8f0fe), slate border (#94a3b8), and `pointer-events: none`
- [x] 2.2 Append a centered `text` label inside each station group showing `station.name` (12px, semi-bold, #475569)
- [x] 2.3 Write tests: verify correct number of `g.station` groups rendered, verify each has a `rect` and `text` child, verify SVG ordering (stations before edges)

## 3. Non-interactivity & Integration

- [x] 3.1 Ensure station rectangles have `pointer-events: none` so clicks pass through to platforms underneath
- [x] 3.2 Verify existing platform click, hover, and tooltip behavior is unchanged with station rectangles present
- [x] 3.3 Run full test suite (`ng test`) and lint (`ng lint`) to confirm no regressions

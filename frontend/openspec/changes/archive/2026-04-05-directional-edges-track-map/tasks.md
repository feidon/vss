## 1. Add arrowhead marker and apply to edges

- [x] 1.1 Add SVG `<defs>` with `<marker>` arrowhead definition in the `render()` method of `TrackMapEditorComponent`
- [x] 1.2 Add `marker-end` attribute to all edge `<line>` elements referencing the marker
- [x] 1.3 Tune `refX` offset so arrowheads don't overlap node circles (r=12) or junction dots (r=4)

## 2. Tests

- [x] 2.1 Add test: SVG `<defs>` contains a `<marker>` element with `orient="auto"`
- [x] 2.2 Add test: all edge `<line>` elements have `marker-end` attribute
- [x] 2.3 Run existing tests to verify no regressions in click/hover/queue behavior

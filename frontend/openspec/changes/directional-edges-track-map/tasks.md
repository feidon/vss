## 1. Add arrowhead marker and apply to edges

- [ ] 1.1 Add SVG `<defs>` with `<marker>` arrowhead definition in the `render()` method of `TrackMapEditorComponent`
- [ ] 1.2 Add `marker-end` attribute to all edge `<line>` elements referencing the marker
- [ ] 1.3 Tune `refX` offset so arrowheads don't overlap node circles (r=12) or junction dots (r=4)

## 2. Tests

- [ ] 2.1 Add test: SVG `<defs>` contains a `<marker>` element with `orient="auto"`
- [ ] 2.2 Add test: all edge `<line>` elements have `marker-end` attribute
- [ ] 2.3 Run existing tests to verify no regressions in click/hover/queue behavior

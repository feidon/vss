## 1. Implement perpendicular label offset

- [x] 1.1 Replace fixed -8px vertical offset with perpendicular offset calculation in `TrackMapEditorComponent.render()` — compute edge direction vector, derive left-side normal, apply 8px offset along normal for label x,y positioning
- [x] 1.2 Verify visually that B8/B10 and B4/B13 labels no longer overlap and horizontal edge labels still appear above the line

## 2. Tests

- [x] 2.1 Add test with crossing edges (shared midpoint) verifying labels have distinct positions
- [x] 2.2 Run existing tests to confirm no regressions

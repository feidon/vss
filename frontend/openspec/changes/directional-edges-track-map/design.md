## Context

The `TrackMapEditorComponent` renders edges as plain `<line>` elements between nodes using d3.js. The `Edge` model already carries `from_id` and `to_id`, meaning direction data exists but is not visually represented. Blocks in the track network are unidirectional, so showing direction helps users understand valid routes.

Current rendering (lines 101–134 of `track-map-editor.ts`):
- Edges are drawn as `<line>` elements with stroke `#94a3b8`
- Block name labels are placed at edge midpoints
- No SVG markers or arrowheads exist

## Goals / Non-Goals

**Goals:**
- Add arrowhead markers to edge lines indicating direction (from → to)
- Arrowheads should be visually clear but not overly prominent
- No regression to existing click, hover, or stop queue behavior

**Non-Goals:**
- Changing the config/overview track map component
- Modifying the Edge data model or API
- Adding bidirectional or animated edges
- Changing edge label positioning

## Decisions

### 1. SVG `<marker>` for arrowheads

**Decision**: Define an SVG `<defs><marker>` element and reference it via `marker-end` on each edge `<line>`.

**Rationale**: This is the standard SVG approach for line endings. D3.js supports it natively — no extra libraries needed. The marker auto-rotates to match line angle.

**Alternatives considered**:
- **Manual triangle `<polygon>` per edge**: More code, must calculate rotation manually, harder to maintain.
- **CSS-based arrow (clip-path/border trick)**: Not applicable to SVG `<line>` elements.

### 2. Arrowhead sizing and position

**Decision**: Small arrowhead (viewBox `0 0 10 10`, refX offset to stop at node edge). Color matches the line stroke (`#94a3b8`). The `refX` value will be tuned to avoid overlap with node circles (radius 12) and junction dots (radius 4).

**Rationale**: Subtle arrows convey direction without cluttering the map. Matching color keeps visual consistency.

### 3. Scope limited to TrackMapEditorComponent

**Decision**: Only modify `track-map-editor.ts` and its test file. The config overview track map is unaffected.

**Rationale**: The config map is read-only and doesn't need direction indicators for its use case.

## Risks / Trade-offs

- **Arrow clipping on short edges**: Very short edges may have overlapping arrowheads and labels → Mitigation: tune `refX` so the arrowhead sits just before the target node's circle/dot boundary.
- **jsdom marker support in tests**: jsdom may not fully render SVG markers → Mitigation: test for the presence of `<marker>` in `<defs>` and `marker-end` attribute on lines, not visual rendering.

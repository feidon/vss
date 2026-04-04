## Context

The `TrackMapEditorComponent` renders platforms and yards as individual d3.js circles. The `GraphResponse` already includes a `stations` array where each `Station` has `platform_ids` grouping platforms together, but this data is not visualized. The reference diagram (`track_map.png`) shows stations as light-filled rounded rectangles that frame their member platforms with a centered label.

## Goals / Non-Goals

**Goals:**
- Render a background rectangle per station, enclosing its platforms, with a station name label.
- Station rectangles appear behind all edges, junctions, and nodes (lowest SVG layer after clearing).
- Style matches the reference: light fill (#e8f0fe / similar), subtle border (#94a3b8), rounded corners.

**Non-Goals:**
- Station rectangles are not interactive (no click, hover, or tooltip).
- No new components or services — all changes are within the existing `render()` method of `TrackMapEditorComponent`.
- No API or model changes.

## Decisions

### 1. Bounding box computation from platform positions
**Decision:** For each `Station`, look up its `platform_ids` in the node list, compute the bounding box of those platforms' scaled (x, y) positions, and add padding.

**Rationale:** This is the simplest approach — no layout engine needed. Platform positions are already available in `posMap` and the scales are already defined.

**Alternative considered:** Using d3 `getBBox()` after rendering platform nodes first, then inserting rects. Rejected because it requires two rendering passes and SVG DOM measurement, which is fragile with jsdom in tests.

### 2. SVG layering order
**Decision:** Render station rectangles immediately after clearing the SVG (before edges, junctions, and nodes).

**Rationale:** SVG uses painter's model (later elements render on top). Drawing station rects first ensures they sit behind all other elements.

### 3. Station label placement
**Decision:** Place the station name label centered within the bounding rectangle, using a semi-bold font at 12px.

**Rationale:** Matches the reference image where station names (S1, S2, S3, Y) appear centered in their rectangles.

### 4. Padding and sizing
**Decision:** Use a padding of 30px around the bounding box of platforms within each station. This provides visual breathing room and ensures the rectangle clearly frames its platforms.

**Alternative considered:** Dynamic padding based on node count. Rejected — fixed padding is simpler and the network is small enough (max 2 platforms per station) that it works uniformly.

## Risks / Trade-offs

- **Single-platform stations (Y):** The yard has only one platform, so its bounding box collapses to a point. → **Mitigation:** Enforce a minimum rectangle size (e.g., 60×60px) so single-node stations still render a visible rectangle.
- **Platform positions very close together:** If two platforms in a station have nearly identical x/y, the rectangle may be very thin. → **Mitigation:** The minimum size handles this case.
- **Test coverage with jsdom:** d3 SVG rendering in jsdom can be limited. → **Mitigation:** Test that the correct number of `g.station` groups are appended with expected attributes, rather than visual pixel testing.

## Context

The schedule editor page has three visual bugs after recent fix attempts:

1. **Timetable node names**: `RouteEditorComponent.nodeName()` (route-editor.ts:132) searches `graph().nodes` and `graph().edges` for node names. The timetable entries include block node IDs, but the lookup may fail if the block's ID in the timetable doesn't match any edge ID in the graph. Meanwhile, `service().route` contains all nodes (including blocks) with correct names, but isn't searched. The `Node` type union (`PlatformNode | YardNode`) also doesn't include `BlockNode`, so block data from the API route response is untyped.

2. **Arrowheads not rendering**: SVG `<marker>` definition exists (track-map-editor.ts:101-114) and `marker-end` is applied (line 132), but arrows aren't visually appearing. Likely causes: marker size too small (6x6) relative to edge lines, `refX=8` not accounting for target node radius (12), and arrowhead color matching the line making it nearly invisible.

3. **Edge label overlap**: Perpendicular offset of 10px (track-map-editor.ts:135) is mathematically correct but practically insufficient. Text labels like "B13" are ~25px wide; two labels 10px apart still overlap.

## Goals / Non-Goals

**Goals:**
- All timetable entries display human-readable node names (never raw UUIDs)
- Arrowheads are clearly visible on all directional edges
- Edge labels are readable without overlapping

**Non-Goals:**
- Changing the track network layout algorithm
- Adding zoom/pan or other new track map features
- Backend API changes

## Decisions

### 1. Build unified name lookup map from service route

**Decision**: In `RouteEditorComponent.nodeName()`, search `service().route` first (which includes all node types from the API response), then fall back to `graph().edges`, then raw ID. Add `BlockNode` interface to the `Node` type union so block data from the route is properly typed.

**Rationale**: The `service().route` array is the most authoritative source for node names in the context of a service — the backend explicitly includes all intermediate block nodes. Searching graph edges as a fallback covers edge cases where a timetable node_id references a block not in the route.

**Alternative considered**: Only searching `graph.edges` (current approach) — insufficient because edge IDs may not match timetable node_ids in all cases.

### 2. Increase marker size and adjust refX for node radius

**Decision**: Increase `markerWidth`/`markerHeight` to 8, use a darker fill color (`#64748b` — slate-500) for contrast against the lighter line color (`#94a3b8`), and calculate `refX` dynamically based on the target node's radius. Shorten the edge line endpoint to stop before the node circle boundary so the arrowhead sits at the edge of the node.

**Rationale**: The current 6x6 marker with matching line color is too subtle. The `refX=8` assumes a fixed offset but doesn't account for the 12px node radius, causing arrows to be hidden behind node circles.

**Alternative considered**: Using CSS to style markers — rejected because SVG marker styling has poor cross-browser support. Using separate arrow elements instead of markers — rejected as more complex with no clear benefit.

### 3. Index-based label staggering with increased base offset

**Decision**: Increase the base perpendicular offset from 10px to 14px. Additionally, group edges that share the same endpoint pair (regardless of direction) and apply an index-based multiplier to the offset so parallel/overlapping edges get progressively larger offsets.

**Rationale**: A fixed 10px offset doesn't account for text bounding box width (~25px for "B13"). Index-based staggering naturally separates labels for crossing edges (like B4/B13 at the S2-S1 junction and B1/B2 at the S1-Y junction).

**Alternative considered**: Collision detection with force-directed label placement — rejected as over-engineered for a fixed 14-block network. Simple staggering is sufficient and predictable.

## Risks / Trade-offs

- **[Risk] Block IDs may not match between route and timetable**: Mitigated by searching multiple sources (route, edges) and falling back to raw ID. If names still show UUIDs, it indicates a backend data issue.
- **[Risk] Increased label offset may push labels too far from edges**: Mitigated by keeping the base offset moderate (14px) and only adding the stagger for edges sharing endpoints.
- **[Trade-off] Adding BlockNode to Node union**: Broadens the type, which means type guards for `node.type` checks need to handle `'block'` — but this is correct since the API already sends block-type nodes.

## Context

The `TrackMapEditorComponent` positions block name labels at edge midpoints with a fixed -8px vertical offset (`yScale(midY) - 8`). For symmetric crossing edges like B8/B10 (S3 junction) and B4/B13 (S2-S1 junction), the midpoints are identical, causing labels to stack on top of each other.

The crossing geometry:
- B8: (225,40) → (50,160), midpoint = (137.5, 100)
- B10: (50,40) → (225,160), midpoint = (137.5, 100)
- B4: (750,160) → (575,40), midpoint = (662.5, 100)
- B13: (575,160) → (750,40), midpoint = (662.5, 100)

## Goals / Non-Goals

**Goals:**
- Separate overlapping edge labels so all block names are readable
- Keep labels visually associated with their edge line

**Non-Goals:**
- Generic collision detection system for arbitrary label overlaps
- Changing label font size or styling
- Adding x,y coordinates to the Edge data model

## Decisions

### 1. Perpendicular offset from edge line

**Decision**: Offset each label perpendicular to its edge direction. Compute a unit normal vector from the edge line and shift the label by a fixed pixel distance (8px) along that normal.

**Rationale**: For crossing edges, perpendicular offsets naturally separate labels because the edges have different angles. B8 (diagonal down-right) pushes its label one way; B10 (diagonal up-right) pushes its label the other way. This is geometry-driven, not special-cased.

**Alternatives considered**:
- **Collision detection + nudging**: More complex, requires iterating over all labels to detect overlaps and resolve them. Overkill for a fixed track topology.
- **Fixed alternating offsets**: Would require detecting which edges overlap. Fragile if topology changes.

### 2. Consistent perpendicular direction

**Decision**: Always offset to the same side of the edge (e.g., left side when traveling from→to). Use the perpendicular normal `(-dy, dx)` normalized, which gives a consistent "left of travel" offset.

**Rationale**: Consistent side selection ensures labels don't jump around unpredictably. For crossing edges, "left of travel" naturally places labels on opposite sides of the crossing point.

## Risks / Trade-offs

- **Labels may shift for non-overlapping edges too**: All labels move from "above midpoint" to "perpendicular to edge" — but this is a visual improvement since labels now hug their own edge line. For horizontal edges, the perpendicular offset is purely vertical (same behavior as current -8px).
- **Very short edges**: Perpendicular offset on very short edges could place labels oddly → Mitigation: the track network has no extremely short edges; minimum length is well above the offset distance.

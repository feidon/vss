## ADDED Requirements

### Requirement: Edge labels offset perpendicular to edge direction
Each edge label SHALL be positioned at the edge midpoint, offset perpendicular to the edge line direction. The offset SHALL be applied along the left-side normal vector (relative to the from→to direction) by a fixed pixel distance.

#### Scenario: Crossing edge labels do not overlap
- **WHEN** the track map renders edges B8 and B10 (symmetric X-crossing at S3)
- **THEN** the labels "B8" and "B10" SHALL be at visually distinct positions, not overlapping

#### Scenario: Crossing edge labels at S2-S1 do not overlap
- **WHEN** the track map renders edges B4 and B13 (symmetric X-crossing at S2-S1)
- **THEN** the labels "B4" and "B13" SHALL be at visually distinct positions, not overlapping

#### Scenario: Horizontal edge labels remain above the line
- **WHEN** the track map renders a horizontal edge (from.y == to.y)
- **THEN** the label SHALL appear above the line (the perpendicular offset for a horizontal line is purely vertical)

#### Scenario: Label stays visually associated with its edge
- **WHEN** any edge label is rendered
- **THEN** the label SHALL be positioned close to the edge midpoint, within a small perpendicular offset distance

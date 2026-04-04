## ADDED Requirements

### Requirement: Edge arrowhead marker definition
The track map editor SHALL define an SVG `<marker>` element in `<defs>` that renders a triangular arrowhead. The marker SHALL use the same color as the edge stroke (`#94a3b8`) and SHALL auto-orient to match line direction.

#### Scenario: Marker defined in SVG defs
- **WHEN** the track map renders with graph data
- **THEN** the SVG contains a `<defs>` element with a `<marker>` child that has `orient="auto"` and contains a filled arrow path

### Requirement: Edges display directional arrowheads
Each edge line SHALL display an arrowhead at the `to_id` end using the `marker-end` attribute referencing the defined marker. The arrowhead SHALL point from `from_id` toward `to_id`.

#### Scenario: All edges have arrowheads
- **WHEN** the track map renders edges
- **THEN** every edge `<line>` element has a `marker-end` attribute referencing the arrowhead marker

#### Scenario: Arrow direction matches from/to
- **WHEN** an edge has `from_id` = "P1A" and `to_id` = "J1"
- **THEN** the arrowhead points from P1A toward J1 (at the line's x2,y2 end)

### Requirement: Arrowheads do not obscure nodes
The arrowhead marker SHALL be offset (via `refX`) so it does not overlap with the target node's circle or junction dot.

#### Scenario: Arrow does not overlap target node
- **WHEN** an edge terminates at a platform or yard node (radius 12)
- **THEN** the arrowhead tip stops before the node circle boundary

#### Scenario: Arrow does not overlap junction dot
- **WHEN** an edge terminates at a junction (radius 4)
- **THEN** the arrowhead tip stops before the junction dot boundary

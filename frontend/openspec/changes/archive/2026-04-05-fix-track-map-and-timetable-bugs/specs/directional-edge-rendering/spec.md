## MODIFIED Requirements

### Requirement: Edge arrowhead marker definition
The track map editor SHALL define an SVG `<marker>` element in `<defs>` that renders a triangular arrowhead. The marker SHALL use a darker color (`#64748b` slate-500) than the edge stroke for visual contrast and SHALL auto-orient to match line direction. The marker SHALL have `markerWidth` and `markerHeight` of at least 8 to be clearly visible.

#### Scenario: Marker defined in SVG defs
- **WHEN** the track map renders with graph data
- **THEN** the SVG contains a `<defs>` element with a `<marker>` child that has `orient="auto"`, `markerWidth` >= 8, `markerHeight` >= 8, and contains a filled arrow path with a darker color than the edge lines

### Requirement: Edges display directional arrowheads
Each edge line SHALL display an arrowhead at the `to_id` end using the `marker-end` attribute referencing the defined marker. The arrowhead SHALL point from `from_id` toward `to_id`. Edge lines SHALL be shortened so the arrowhead tip sits at the boundary of the target node circle, not behind it.

#### Scenario: All edges have arrowheads
- **WHEN** the track map renders edges
- **THEN** every edge `<line>` element has a `marker-end` attribute referencing the arrowhead marker

#### Scenario: Arrow direction matches from/to
- **WHEN** an edge has `from_id` = "P1A" and `to_id` = "J1"
- **THEN** the arrowhead points from P1A toward J1 (at the line's x2,y2 end)

### Requirement: Arrowheads do not obscure nodes
The edge line endpoint (x2, y2) SHALL be pulled back by the target node's radius so the arrowhead renders at the circle boundary. Platform and yard nodes have radius 12; junction dots have radius 4.

#### Scenario: Arrow does not overlap target node
- **WHEN** an edge terminates at a platform or yard node (radius 12)
- **THEN** the line endpoint is shortened by 12 pixels along the edge direction so the arrowhead tip touches the node circle boundary

#### Scenario: Arrow does not overlap junction dot
- **WHEN** an edge terminates at a junction (radius 4)
- **THEN** the line endpoint is shortened by 4 pixels along the edge direction so the arrowhead tip touches the junction dot boundary

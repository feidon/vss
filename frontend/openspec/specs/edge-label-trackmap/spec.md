## ADDED Requirements

### Requirement: Blocks render as edge labels, not nodes
The editor track map SHALL NOT render block nodes as SVG circles. Instead, block names SHALL be rendered as text labels positioned at the block's x/y coordinates on the connection edges.

#### Scenario: Block circles are absent
- **WHEN** the track map renders a graph containing block nodes
- **THEN** no SVG `<circle>` elements with class `block` SHALL be present in the SVG

#### Scenario: Block names appear as edge labels
- **WHEN** the track map renders a graph containing block nodes
- **THEN** each block's name SHALL appear as an SVG `<text>` element positioned at the block's x/y coordinates (scaled to SVG space)

#### Scenario: Edge labels are non-interactive
- **WHEN** the user hovers over or clicks a block edge label
- **THEN** no tooltip, hover feedback, or click event SHALL be emitted

### Requirement: Connections still draw between all linked nodes
The track map SHALL continue to draw SVG `<line>` elements for all connections in the graph. The visual edges between platforms, blocks, and yards SHALL remain unchanged.

#### Scenario: Connection lines are preserved
- **WHEN** the track map renders a graph with connections
- **THEN** all connections SHALL render as SVG `<line>` elements connecting the from/to node coordinates

### Requirement: Platforms and yards remain interactive nodes
Platforms and yards SHALL continue to render as clickable circle nodes with queue indicators, hover feedback, and tooltips. No change from current behavior.

#### Scenario: Platform click emits stop event
- **WHEN** the user clicks a platform node on an interactive track map
- **THEN** a `stopAdded` event SHALL be emitted with the platform's node ID and name

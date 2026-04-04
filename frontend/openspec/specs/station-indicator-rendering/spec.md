### Requirement: Station rectangles render behind platforms
The track map SHALL render a rounded rectangle for each station in `GraphResponse.stations`, positioned behind all edges, junctions, and platform nodes. Each rectangle SHALL enclose all platforms listed in that station's `platform_ids`.

#### Scenario: Multi-platform station rendering
- **WHEN** the graph contains a station with 2 platform_ids (e.g., S1 with P1A and P1B)
- **THEN** a single rounded rectangle SHALL appear behind P1A and P1B, enclosing both platform circles with padding

#### Scenario: Single-platform station rendering
- **WHEN** the graph contains a station with 1 platform_id (e.g., Y with only the yard node)
- **THEN** a rounded rectangle SHALL appear with a minimum size (at least 60×60px) so it is clearly visible

#### Scenario: SVG layer ordering
- **WHEN** the track map renders
- **THEN** station rectangles SHALL appear in the SVG before edges, junctions, and nodes (i.e., rendered first so they sit behind everything)

### Requirement: Station rectangles display station name
Each station rectangle SHALL display the station's `name` as a centered text label inside the rectangle.

#### Scenario: Station label text
- **WHEN** a station named "S1" is rendered
- **THEN** the text "S1" SHALL appear centered within the station rectangle

#### Scenario: Yard station label
- **WHEN** a station with `is_yard: true` named "Y" is rendered
- **THEN** the text "Y" SHALL appear centered within the station rectangle (same treatment as regular stations)

### Requirement: Station rectangles are non-interactive
Station rectangles SHALL NOT respond to mouse events. Click and hover interactions SHALL only apply to platform/yard nodes, not to the station background rectangles.

#### Scenario: Clicking on station rectangle area
- **WHEN** a user clicks on the station rectangle background (not on a platform circle)
- **THEN** no stop SHALL be added and no event SHALL be emitted

#### Scenario: Hovering over station rectangle
- **WHEN** a user hovers over the station rectangle background
- **THEN** no tooltip SHALL appear and no visual hover feedback SHALL occur on the rectangle

### Requirement: Station rectangle styling
Station rectangles SHALL have a light fill color, a subtle border, and rounded corners consistent with the reference design.

#### Scenario: Visual styling
- **WHEN** a station rectangle is rendered
- **THEN** it SHALL have a light blue/gray fill, a slate-colored border stroke, and border-radius for rounded corners

### Requirement: All stations from GraphResponse are rendered
The track map SHALL render a rectangle for every station in `GraphResponse.stations`, regardless of how many platforms each station contains.

#### Scenario: Complete station coverage
- **WHEN** the graph contains 4 stations (Y, S1, S2, S3)
- **THEN** exactly 4 station rectangles SHALL be rendered

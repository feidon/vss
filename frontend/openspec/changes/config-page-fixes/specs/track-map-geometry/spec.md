## MODIFIED Requirements

### Requirement: Track map node geometry coordinates
The system SHALL define x,y coordinates for all 21 network nodes (14 blocks, 6 platforms, 1 yard) that visually represent the railway topology. The layout SHALL follow a left-to-right arrangement: S3 (leftmost) -> S2 (center) -> S1 (right) -> Y (far right), with upper and lower tracks and crossover blocks at station junctions. The graph data SHALL be available via a dedicated `GET /api/graph` endpoint so that the config page track map overview can load it independently of any service.

#### Scenario: All nodes have coordinates
- **WHEN** the graph is loaded from `GET /api/services/{id}` or `GET /api/graph`
- **THEN** every node in the response SHALL have x and y coordinates that position it correctly on the track map

#### Scenario: Config page track map loads successfully
- **WHEN** the config page track map overview component initializes
- **THEN** it SHALL fetch graph data from `GET /api/graph` and render the track map with all nodes at their correct positions

#### Scenario: GET /api/graph returns valid GraphResponse
- **WHEN** the frontend calls `GET /api/graph`
- **THEN** the backend SHALL return a `GraphResponse` containing nodes (with x,y coordinates), connections, stations, and vehicles

#### Scenario: Track topology is visually correct
- **WHEN** the track map renders nodes at their x,y coordinates
- **THEN** the layout SHALL show:
  - Two horizontal tracks (upper and lower) running left to right
  - Platforms at stations: P3A/P3B (left), P2A/P2B (center), P1A/P1B (right)
  - Yard Y at the far right, vertically centered between the two tracks
  - Crossover blocks (B8, B10 at S3; B4, B14 at S2-S1 junction) positioned diagonally between the upper and lower tracks
  - Straight blocks positioned along their respective tracks

#### Scenario: Coordinates are seeded to database
- **WHEN** the database is seeded with node geometry
- **THEN** each node's x,y coordinates SHALL match the reference table defined in the base spec

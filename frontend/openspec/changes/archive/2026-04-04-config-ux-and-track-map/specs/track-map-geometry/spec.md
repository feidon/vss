## ADDED Requirements

### Requirement: Track map node geometry coordinates
The system SHALL define x,y coordinates for all 21 network nodes (14 blocks, 6 platforms, 1 yard) that visually represent the railway topology. The layout SHALL follow a left-to-right arrangement: S3 (leftmost) -> S2 (center) -> S1 (right) -> Y (far right), with upper and lower tracks and crossover blocks at station junctions.

#### Scenario: All nodes have coordinates
- **WHEN** the graph is loaded from GET `/api/services/{id}` or GET `/api/graph`
- **THEN** every node in the response SHALL have x and y coordinates that position it correctly on the track map

#### Scenario: Track topology is visually correct
- **WHEN** the track map renders nodes at their x,y coordinates
- **THEN** the layout SHALL show:
  - Two horizontal tracks (upper and lower) running left to right
  - Platforms at stations: P3A/P3B (left), P2A/P2B (center), P1A/P1B (right)
  - Yard Y at the far right, vertically centered between the two tracks
  - Crossover blocks (B8, B10 at S3; B4, B14 at S2-S1 junction) positioned diagonally between the upper and lower tracks
  - Straight blocks positioned along their respective tracks

### Requirement: Node coordinate reference table
The following x,y coordinates SHALL be seeded into the database for each node. Coordinate space assumes a viewport of approximately 1000x200 units.

**Platforms:**

| Node | x   | y   | Description        |
|------|-----|-----|--------------------|
| P3A  | 50  | 40  | S3 upper platform  |
| P3B  | 50  | 160 | S3 lower platform  |
| P2A  | 400 | 40  | S2 upper platform  |
| P2B  | 400 | 160 | S2 lower platform  |
| P1A  | 750 | 40  | S1 upper platform  |
| P1B  | 750 | 160 | S1 lower platform  |

**Yard:**

| Node | x   | y   | Description |
|------|-----|-----|-------------|
| Y    | 950 | 100 | Yard        |

**Blocks (Group 3 -- S3 junction):**

| Node | x   | y   | Description                    |
|------|-----|-----|--------------------------------|
| B7   | 160 | 40  | Upper track leaving P3A        |
| B8   | 200 | 80  | Crossover upper-to-lower at S3 |
| B9   | 160 | 160 | Lower track leaving P3B        |
| B10  | 200 | 120 | Crossover lower-to-upper at S3 |

**Blocks (Ungrouped -- between S3 and S2):**

| Node | x   | y   | Description              |
|------|-----|-----|--------------------------|
| B6   | 300 | 40  | Upper track S3->S2       |
| B11  | 300 | 160 | Lower track S3->S2       |

**Blocks (Group 2 -- S2/S1 junction):**

| Node | x   | y   | Description                        |
|------|-----|-----|------------------------------------|
| B5   | 510 | 40  | Upper track leaving P2A            |
| B4   | 550 | 80  | Crossover upper-to-lower at S2-S1  |
| B12  | 510 | 160 | Lower track leaving P2B            |
| B14  | 550 | 120 | Crossover lower-to-upper at S2-S1  |
| B3   | 650 | 40  | Upper track arriving P1A           |
| B13  | 650 | 160 | Lower track arriving P1B           |

**Blocks (Group 1 -- S1 to Y):**

| Node | x   | y   | Description          |
|------|-----|-----|----------------------|
| B1   | 850 | 60  | Upper path S1->Y     |
| B2   | 850 | 140 | Lower path S1->Y     |

#### Scenario: Coordinates are seeded to database
- **WHEN** the database is seeded with node geometry
- **THEN** each node's x,y coordinates SHALL match the reference table above

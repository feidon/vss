## ADDED Requirements

### Requirement: Track map renders network topology
The track map editor SHALL render all nodes from the graph response at their `(x, y)` positions using d3.js. Blocks SHALL be displayed as non-interactive path segments. Platforms and yards SHALL be displayed as clickable nodes with distinct styling.

#### Scenario: Map renders with graph data
- **WHEN** the editor loads and graph data is available
- **THEN** all nodes are rendered at their coordinates with connections drawn between them

#### Scenario: Node type distinction
- **WHEN** the map renders
- **THEN** platforms and yards are visually distinct from blocks (e.g., larger circles, different color) and show their name labels

### Requirement: Click platform or yard to add stop
The user SHALL be able to click a platform or yard node on the map to append it to the stop queue. Blocks SHALL NOT be clickable for adding stops.

#### Scenario: Add platform stop by clicking
- **WHEN** user clicks platform node "P1A" on the map
- **THEN** P1A is appended to the stop queue with default dwell time of 30 seconds

#### Scenario: Add yard stop by clicking
- **WHEN** user clicks the yard node "Y" on the map
- **THEN** Y is appended to the stop queue with default dwell time of 30 seconds

#### Scenario: Block nodes are not clickable
- **WHEN** user clicks a block node (e.g., "B3") on the map
- **THEN** nothing is added to the stop queue

### Requirement: Visual feedback on map interaction
The map SHALL provide visual feedback for node interaction: hover highlights the node, and nodes already in the stop queue SHALL be visually marked (e.g., filled color or numbered marker).

#### Scenario: Hover feedback
- **WHEN** user hovers over a platform node
- **THEN** the node is visually highlighted and shows a tooltip with its name

#### Scenario: Queued node indication
- **WHEN** platform P1A is in the stop queue
- **THEN** the P1A node on the map is visually marked as selected (e.g., different fill color or order number overlay)

### Requirement: Stop queue panel alongside map
The stop queue SHALL be displayed in a panel beside the track map, showing the ordered list of selected stops. Each stop SHALL have an editable dwell time input (default 30 seconds) and a remove button. The user SHALL be able to reorder stops.

#### Scenario: Stop queue displays selected stops
- **WHEN** user has added P1A and P2A as stops
- **THEN** the queue panel shows: 1. P1A (dwell: 30s), 2. P2A (dwell: 30s)

#### Scenario: Edit dwell time
- **WHEN** user changes P1A's dwell time to 60
- **THEN** the stop queue reflects dwell time of 60 seconds for P1A

#### Scenario: Remove stop from queue
- **WHEN** user clicks the remove button on P1A
- **THEN** P1A is removed from the queue and the map node reverts to unselected styling

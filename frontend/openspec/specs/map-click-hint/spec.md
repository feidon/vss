## ADDED Requirements

### Requirement: Hint text guides users to click the map
The track map editor SHALL display an instructional hint ("Click a platform or yard on the map to add a stop") when the stop queue is empty. The hint SHALL be hidden once at least one stop has been added.

#### Scenario: Hint visible with empty queue
- **WHEN** the track map editor loads and the stop queue is empty
- **THEN** a hint text "Click a platform or yard on the map to add a stop" is displayed above the map

#### Scenario: Hint hidden after adding first stop
- **WHEN** the user adds a stop to the queue (by clicking a node on the map)
- **THEN** the hint text is no longer visible

#### Scenario: Hint reappears when all stops removed
- **WHEN** the user removes all stops from the queue
- **THEN** the hint text reappears

### Requirement: Clickable nodes show pointer cursor
Platform and yard nodes on the track map SHALL display a pointer cursor on hover to indicate they are clickable.

#### Scenario: Pointer cursor on platform node
- **WHEN** the user hovers over a platform node on the map
- **THEN** the cursor changes to a pointer

#### Scenario: Pointer cursor on yard node
- **WHEN** the user hovers over the yard node on the map
- **THEN** the cursor changes to a pointer

#### Scenario: No pointer cursor on block nodes
- **WHEN** the user hovers over a block node (non-clickable)
- **THEN** the cursor remains the default (no pointer)

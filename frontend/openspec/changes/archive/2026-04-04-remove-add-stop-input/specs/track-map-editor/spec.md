## MODIFIED Requirements

### Requirement: Stop queue panel alongside map
The stop queue SHALL be displayed in a panel beside the track map, showing the ordered list of selected stops. Each stop SHALL have an editable dwell time input (default 30 seconds) and a remove button. The user SHALL be able to reorder stops. Stops SHALL only be added via clicking nodes on the track map — there SHALL be no dropdown select or "Add" button for adding stops.

#### Scenario: Stop queue displays selected stops
- **WHEN** user has added P1A and P2A as stops via map clicks
- **THEN** the queue panel shows: 1. P1A (dwell: 30s), 2. P2A (dwell: 30s)

#### Scenario: Edit dwell time
- **WHEN** user changes P1A's dwell time to 60
- **THEN** the stop queue reflects dwell time of 60 seconds for P1A

#### Scenario: Remove stop from queue
- **WHEN** user clicks the remove button on P1A
- **THEN** P1A is removed from the queue and the map node reverts to unselected styling

#### Scenario: No dropdown for adding stops
- **WHEN** the stop queue panel is displayed
- **THEN** there is no dropdown select or "Add" button for adding stops

## REMOVED Requirements

### Requirement: Dropdown-based stop addition
**Reason**: Redundant with track map click interaction. The map provides more intuitive spatial context for selecting platforms and yards.
**Migration**: Users add stops by clicking platform or yard nodes directly on the track map. Hint text guides new users to this interaction.

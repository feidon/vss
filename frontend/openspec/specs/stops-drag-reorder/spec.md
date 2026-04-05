### Requirement: Stops list supports drag-and-drop reordering
The route editor's stops list SHALL allow users to reorder stops by dragging and dropping individual rows within the list. The reordered list SHALL become the new stop sequence used for route submission.

#### Scenario: Drag a stop to a new position
- **WHEN** user drags a stop from position 3 to position 1
- **THEN** the stop moves to position 1 and all other stops shift down accordingly
- **THEN** the numbered order indicators update to reflect the new sequence

#### Scenario: Drag handle is visible on each stop row
- **WHEN** the stops list contains one or more stops
- **THEN** each stop row SHALL display a drag handle icon on the left side

#### Scenario: Drop at same position is a no-op
- **WHEN** user drags a stop and drops it back at its original position
- **THEN** the stops list SHALL remain unchanged

### Requirement: Visual feedback during drag
The system SHALL provide visual feedback while a drag operation is in progress so the user can see where the stop will be placed.

#### Scenario: Placeholder shown at drop target
- **WHEN** user is dragging a stop over the list
- **THEN** a placeholder element SHALL appear at the prospective drop position indicating where the item will land

#### Scenario: Dragged item shows a preview
- **WHEN** user is dragging a stop
- **THEN** a visual preview of the stop row SHALL follow the pointer/touch position

### Requirement: Track map order numbers update after reorder
The track map's queued-stop order numbers SHALL update reactively when stops are reordered in the list.

#### Scenario: Map reflects reordered stops
- **WHEN** user reorders stops in the list (e.g., swaps stop 1 and stop 3)
- **THEN** the order numbers displayed on the track map nodes SHALL update to match the new sequence

### Requirement: Existing stop operations remain functional alongside drag-and-drop
Adding, removing, and editing dwell time on stops SHALL continue to work as before with drag-and-drop enabled.

#### Scenario: Add stop after reorder
- **WHEN** user reorders stops and then clicks a new platform on the track map
- **THEN** the new stop SHALL be appended to the end of the reordered list

#### Scenario: Remove stop from reordered list
- **WHEN** user clicks the remove button on a stop in a reordered list
- **THEN** that stop SHALL be removed and remaining stops renumber correctly

#### Scenario: Edit dwell time on reordered stop
- **WHEN** user changes the dwell time input on a stop that was previously reordered
- **THEN** the dwell time SHALL update for that stop without affecting the order

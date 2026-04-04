## ADDED Requirements

### Requirement: Display dash for ungrouped blocks in group column
The system SHALL display "-" in the group data cell for blocks with `group: 0`. Blocks with a non-zero group SHALL continue to display their numeric group value.

#### Scenario: Ungrouped block shows dash
- **WHEN** a block has `group: 0`
- **THEN** the group column for that row SHALL display "-"

#### Scenario: Grouped block shows group number
- **WHEN** a block has `group: 2`
- **THEN** the group column for that row SHALL display "2"

## ADDED Requirements

### Requirement: Display descriptive label for ungrouped blocks
The system SHALL display "Ungrouped" as the group header for blocks with `group: 0` instead of "Group 0". All other groups SHALL continue to display as "Group {n}".

#### Scenario: Blocks with group 0 show "Ungrouped" header
- **WHEN** the block list contains blocks with `group: 0`
- **THEN** the group header for those blocks SHALL display "Ungrouped"

#### Scenario: Blocks with non-zero group show numbered header
- **WHEN** the block list contains blocks with `group: 1` (or any non-zero group)
- **THEN** the group header SHALL display "Group 1" (preserving existing format)

## MODIFIED Requirements

### Requirement: Display all blocks with traversal times
The system SHALL display all blocks in a table showing block name, interlocking group, and traversal time in seconds. Blocks SHALL be grouped by interlocking group with group headers, and sorted in natural numeric order by name within each group. Groups SHALL be sorted by group number (ungrouped/group 0 first, then ascending).

#### Scenario: Blocks are sorted within groups using natural numeric order
- **WHEN** blocks are displayed within a group (e.g., Group 2 contains B3, B4, B13, B14)
- **THEN** blocks SHALL be sorted in natural numeric order by name (B3, B4, B13, B14 — not B13, B14, B3, B4)

#### Scenario: Single-digit block names sort correctly
- **WHEN** a group contains only single-digit block names (e.g., Group 1: B1, B2)
- **THEN** blocks SHALL appear in ascending numeric order (B1, B2)

#### Scenario: Mixed single and multi-digit block names sort correctly
- **WHEN** a group contains both single-digit and multi-digit block names (e.g., Group 3: B7, B8, B9, B10)
- **THEN** blocks SHALL appear in natural numeric order (B7, B8, B9, B10 — not B10, B7, B8, B9)

#### Scenario: Groups are sorted
- **WHEN** the block table is rendered
- **THEN** groups SHALL appear in ascending order by group number (Ungrouped first, then Group 1, Group 2, Group 3)

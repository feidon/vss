## ADDED Requirements

### Requirement: Stable row height during inline editing
The system SHALL maintain a consistent row height for block rows regardless of whether the traversal time cell is in display mode or edit mode. Entering or exiting edit mode SHALL NOT cause the row to resize.

#### Scenario: Row height unchanged when entering edit mode
- **WHEN** the user clicks a traversal time value to enter edit mode
- **THEN** the row height SHALL remain the same as it was in display mode

#### Scenario: Row height unchanged when exiting edit mode
- **WHEN** the user exits edit mode (via Enter, Escape, or blur)
- **THEN** the row height SHALL remain the same as it was in edit mode

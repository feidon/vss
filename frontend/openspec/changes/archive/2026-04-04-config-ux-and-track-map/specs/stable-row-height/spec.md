## MODIFIED Requirements

### Requirement: Stable row height during inline editing
The system SHALL maintain a consistent row height for block rows regardless of whether the traversal time cell is in display mode or edit mode. The row height SHALL be set large enough to contain the input field. Entering or exiting edit mode SHALL NOT cause the row or any surrounding rows to resize or shift.

#### Scenario: Row height unchanged when entering edit mode
- **WHEN** the user clicks a traversal time value to enter edit mode
- **THEN** the row height SHALL remain the same as it was in display mode, with no layout shift of adjacent rows

#### Scenario: Row height unchanged when exiting edit mode
- **WHEN** the user exits edit mode (via Enter, Escape, or blur)
- **THEN** the row height SHALL remain the same as it was in edit mode

#### Scenario: Input field fits within row
- **WHEN** the traversal time cell is in edit mode
- **THEN** the input field height SHALL NOT exceed the row height, and the row separation lines SHALL remain at the same vertical positions

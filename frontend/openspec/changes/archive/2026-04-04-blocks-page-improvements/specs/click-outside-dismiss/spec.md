## MODIFIED Requirements

### Requirement: Click outside edit input saves and closes editing
When the user is editing a block's traversal time and clicks anywhere outside the input field, the system SHALL validate and save the value. If validation fails, the system SHALL keep the edit input open and display the validation error.

#### Scenario: User clicks outside input to save
- **WHEN** the user is editing a block's traversal time and clicks outside the input field
- **THEN** the system SHALL validate and save the new value, then close the edit input

#### Scenario: User clicks outside with invalid value
- **WHEN** the user is editing a block's traversal time, has entered an invalid value, and clicks outside the input field
- **THEN** the edit input SHALL remain open and the validation error SHALL be displayed

#### Scenario: User presses Enter to save
- **WHEN** the user is editing a block's traversal time and presses the Enter key
- **THEN** the system SHALL validate and save the new value (existing behavior preserved)

#### Scenario: User presses Escape to cancel
- **WHEN** the user is editing a block's traversal time and presses the Escape key
- **THEN** the edit input SHALL close and the original value SHALL be restored without saving (existing behavior preserved)

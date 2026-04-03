## ADDED Requirements

### Requirement: Click outside edit input cancels editing
When the user is editing a block's traversal time and clicks anywhere outside the input field, the system SHALL cancel the edit and revert the displayed value to the original. The system SHALL NOT save the value on blur.

#### Scenario: User clicks outside input to dismiss
- **WHEN** the user is editing a block's traversal time and clicks outside the input field
- **THEN** the edit input SHALL close and the original value SHALL be restored without saving

#### Scenario: User presses Enter to save
- **WHEN** the user is editing a block's traversal time and presses the Enter key
- **THEN** the system SHALL validate and save the new value (existing behavior preserved)

#### Scenario: User presses Escape to cancel
- **WHEN** the user is editing a block's traversal time and presses the Escape key
- **THEN** the edit input SHALL close and the original value SHALL be restored without saving (existing behavior preserved)

#### Scenario: User tabs away from input
- **WHEN** the user is editing a block's traversal time and presses Tab (causing blur)
- **THEN** the edit input SHALL close and the original value SHALL be restored without saving

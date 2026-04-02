## MODIFIED Requirements

### Requirement: Inline editing of traversal time
The system SHALL allow the user to edit a block's traversal time by clicking on the traversal time value or an adjacent pencil icon. The traversal time cell SHALL display a pencil icon beside the value to indicate editability. The value SHALL switch to an editable input field. The user SHALL be able to save the new value by pressing Enter or blurring the field, and cancel by pressing Escape.

#### Scenario: Edit affordance is visible
- **WHEN** the block configuration table is displayed
- **THEN** each traversal time cell shows a pencil icon next to the time value

#### Scenario: Pencil icon indicates hover state
- **WHEN** the user hovers over a traversal time cell
- **THEN** the pencil icon changes color to indicate interactivity

#### Scenario: Enter edit mode via icon click
- **WHEN** the user clicks the pencil icon next to a block's traversal time
- **THEN** the value is replaced with a number input field pre-filled with the current traversal time

#### Scenario: Enter edit mode via value click
- **WHEN** the user clicks on a block's traversal time value
- **THEN** the value is replaced with a number input field pre-filled with the current traversal time

#### Scenario: Save on Enter
- **WHEN** the user is editing a traversal time and presses Enter
- **THEN** the system sends PATCH `/blocks/{id}` with the new `traversal_time_seconds` value and exits edit mode

#### Scenario: Save on blur
- **WHEN** the user is editing a traversal time and clicks outside the input (blur)
- **THEN** the system sends PATCH `/blocks/{id}` with the new `traversal_time_seconds` value and exits edit mode

#### Scenario: Cancel on Escape
- **WHEN** the user is editing a traversal time and presses Escape
- **THEN** the input reverts to the original value and exits edit mode without making an API call

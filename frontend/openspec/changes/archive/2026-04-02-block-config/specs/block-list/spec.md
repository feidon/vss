## ADDED Requirements

### Requirement: Display all blocks with traversal times
The system SHALL display all blocks in a table showing block name, interlocking group, and traversal time in seconds. Blocks SHALL be grouped by interlocking group with group headers, and sorted by name within each group.

#### Scenario: Blocks load successfully
- **WHEN** the user navigates to the block configuration page
- **THEN** the system fetches all blocks from GET `/blocks` and displays them in a grouped table

#### Scenario: Blocks fail to load
- **WHEN** the API request to GET `/blocks` fails
- **THEN** the system displays an error message indicating blocks could not be loaded

### Requirement: Inline editing of traversal time
The system SHALL allow the user to edit a block's traversal time by clicking on the traversal time value. The value SHALL switch to an editable input field. The user SHALL be able to save the new value by pressing Enter or blurring the field, and cancel by pressing Escape.

#### Scenario: Enter edit mode
- **WHEN** the user clicks on a block's traversal time value
- **THEN** the value is replaced with a number input field pre-filled with the current traversal time and the input is focused

#### Scenario: Save on Enter
- **WHEN** the user is editing a traversal time and presses Enter
- **THEN** the system sends PATCH `/blocks/{id}` with the new `traversal_time_seconds` value and exits edit mode

#### Scenario: Save on blur
- **WHEN** the user is editing a traversal time and clicks outside the input (blur)
- **THEN** the system sends PATCH `/blocks/{id}` with the new `traversal_time_seconds` value and exits edit mode

#### Scenario: Cancel on Escape
- **WHEN** the user is editing a traversal time and presses Escape
- **THEN** the input reverts to the original value and exits edit mode without making an API call

### Requirement: Client-side validation of traversal time
The system SHALL validate that the entered traversal time is a positive integer (minimum 1). The system SHALL NOT send the API request if validation fails.

#### Scenario: Invalid input rejected
- **WHEN** the user enters a value less than 1, a non-integer, or an empty value
- **THEN** the system does not send the PATCH request and shows a validation error near the input

#### Scenario: Valid input accepted
- **WHEN** the user enters a positive integer >= 1
- **THEN** the system proceeds with the PATCH request

### Requirement: Save feedback
The system SHALL provide visual feedback after a save attempt. On success, the updated value SHALL be displayed. On failure, the value SHALL revert to the previous value and an error message SHALL be shown.

#### Scenario: Successful save
- **WHEN** the PATCH request succeeds
- **THEN** the table displays the updated traversal time value

#### Scenario: Failed save
- **WHEN** the PATCH request fails
- **THEN** the traversal time reverts to its previous value and an error message is displayed to the user

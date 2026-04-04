### Requirement: Display all blocks with traversal times
The system SHALL display all blocks in a table showing block name, interlocking group, and traversal time in seconds. Blocks SHALL be grouped by interlocking group with group headers, and sorted in natural numeric order by name within each group. Groups SHALL be sorted by group number (ungrouped/group 0 first, then ascending).

#### Scenario: Blocks load successfully
- **WHEN** the user navigates to the block configuration page
- **THEN** the system fetches all blocks from GET `/blocks` and displays them in a grouped table

#### Scenario: Blocks are sorted within groups using natural numeric order
- **WHEN** blocks are displayed within a group (e.g., Group 2 contains B3, B4, B13, B14)
- **THEN** blocks SHALL be sorted in natural numeric order by name (B3, B4, B13, B14 — not B13, B14, B3, B4)

#### Scenario: Groups are sorted
- **WHEN** the block table is rendered
- **THEN** groups SHALL appear in ascending order by group number (Ungrouped first, then Group 1, Group 2, Group 3)

#### Scenario: Blocks fail to load
- **WHEN** the API request to GET `/blocks` fails
- **THEN** the system displays an error message indicating blocks could not be loaded

### Requirement: Inline editing of traversal time
The system SHALL allow the user to edit a block's traversal time by clicking on the traversal time value or the pencil icon. The pencil icon SHALL be positioned at a fixed location to the right of the traversal time value, separated by a small gap. The icon SHALL remain visible in both display and edit modes. In display mode, clicking the icon or value opens the input. In edit mode, clicking the icon closes the input (saving the value).

#### Scenario: Edit affordance is visible
- **WHEN** the block configuration table is displayed
- **THEN** each traversal time cell shows the numeric value followed by a pencil icon at a fixed position to its right

#### Scenario: Pencil icon indicates hover state
- **WHEN** the user hovers over the pencil icon
- **THEN** the icon changes color to indicate interactivity

#### Scenario: Enter edit mode via icon click
- **WHEN** the user clicks the pencil icon next to a block's traversal time (while not editing)
- **THEN** the value is replaced with a number input field pre-filled with the current traversal time, and the pencil icon remains visible to the right of the input

#### Scenario: Enter edit mode via value click
- **WHEN** the user clicks on a block's traversal time value
- **THEN** the value is replaced with a number input field pre-filled with the current traversal time, and the pencil icon remains visible to the right of the input

#### Scenario: Close edit mode via icon click
- **WHEN** the user is in edit mode and clicks the pencil icon
- **THEN** the system SHALL validate and save the value, then close the input field

#### Scenario: Save on Enter
- **WHEN** the user is editing a traversal time and presses Enter
- **THEN** the system sends PATCH `/blocks/{id}` with the new `traversal_time_seconds` value and exits edit mode

#### Scenario: Save on blur
- **WHEN** the user is editing a traversal time and the input loses focus (blur)
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

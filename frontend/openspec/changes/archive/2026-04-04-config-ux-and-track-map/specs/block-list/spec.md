## MODIFIED Requirements

### Requirement: Display all blocks with traversal times
The system SHALL display all blocks in a table showing block name, interlocking group, and traversal time in seconds. Blocks SHALL be grouped by interlocking group with group headers, and sorted by name within each group. Groups SHALL be sorted by group number (ungrouped/group 0 first, then ascending).

#### Scenario: Blocks load successfully
- **WHEN** the user navigates to the block configuration page
- **THEN** the system fetches all blocks from GET `/blocks` and displays them in a grouped table

#### Scenario: Blocks are sorted within groups
- **WHEN** blocks are displayed within a group
- **THEN** blocks SHALL be sorted alphabetically by name (e.g., B1 before B2, B3 before B4)

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

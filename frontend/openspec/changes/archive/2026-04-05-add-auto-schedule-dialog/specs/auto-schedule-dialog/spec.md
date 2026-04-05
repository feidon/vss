## ADDED Requirements

### Requirement: Auto Schedule button in schedule list header
The schedule list page SHALL display an "Auto Schedule" button in the header area alongside the existing "Create Service" button.

#### Scenario: Button is visible on page load
- **WHEN** the user navigates to the schedule list page
- **THEN** an "Auto Schedule" button SHALL be visible in the header

### Requirement: Clicking Auto Schedule opens dialog
The system SHALL open the `AutoScheduleDialogComponent` when the user clicks the "Auto Schedule" button.

#### Scenario: Dialog opens on button click
- **WHEN** the user clicks the "Auto Schedule" button
- **THEN** a modal dialog SHALL appear with a form for generation parameters

### Requirement: Dialog collects generation parameters
The dialog SHALL present a form with four required fields: service interval (seconds), start time, end time, and dwell time (seconds).

#### Scenario: All four fields are present
- **WHEN** the dialog opens
- **THEN** the form SHALL contain inputs for interval_seconds (number), start_time (datetime-local), end_time (datetime-local), and dwell_time_seconds (number)

#### Scenario: Fields have validation
- **WHEN** the user enters invalid values (non-positive interval, non-positive dwell time, or end time not after start time)
- **THEN** the "Generate" button SHALL remain disabled

### Requirement: Destructive action warning
The dialog SHALL display a prominent warning that auto-scheduling will delete all existing services.

#### Scenario: Warning is always visible
- **WHEN** the dialog is open and showing the form
- **THEN** a warning banner SHALL be visible stating that all current services will be removed

### Requirement: Generate button triggers API call
The dialog SHALL call `POST /api/schedules/generate` with the form values when the user clicks "Generate".

#### Scenario: Successful generation
- **WHEN** the user fills in valid parameters and clicks "Generate"
- **THEN** the system SHALL send a POST request with `{ interval_seconds, start_time, end_time, dwell_time_seconds }` and display a success summary showing services_created, vehicles_used count, and cycle_time_seconds

#### Scenario: Loading state during generation
- **WHEN** the API call is in progress
- **THEN** the form controls and buttons SHALL be disabled and a loading indicator SHALL be shown

#### Scenario: API returns error
- **WHEN** the backend returns an error (e.g., SCHEDULE_INFEASIBLE)
- **THEN** the error message SHALL be displayed in the dialog and the user SHALL be able to modify parameters and retry

### Requirement: Dialog close refreshes service list
After successful generation, closing the dialog SHALL refresh the schedule list to show the newly generated services.

#### Scenario: List refreshes on dialog close after success
- **WHEN** the user closes the dialog after a successful generation
- **THEN** the schedule list SHALL reload and display the newly generated services

#### Scenario: List unchanged on cancel
- **WHEN** the user cancels or closes the dialog without generating
- **THEN** the schedule list SHALL remain unchanged

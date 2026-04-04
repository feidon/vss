## ADDED Requirements

### Requirement: Local datetime to UTC epoch conversion
The system SHALL provide a `localDatetimeToEpoch` function that converts an HTML `datetime-local` input string (format `YYYY-MM-DDTHH:mm`) to a UTC epoch timestamp in seconds. The conversion SHALL interpret the input as the browser's local timezone.

#### Scenario: Convert local datetime string to epoch
- **WHEN** `localDatetimeToEpoch("2024-01-15T08:00")` is called in a browser at UTC+0
- **THEN** the function returns `1705305600` (2024-01-15T08:00:00Z)

#### Scenario: Round-trip consistency
- **WHEN** a local datetime string is converted to epoch via `localDatetimeToEpoch` and then back via `epochToLocalDatetime`
- **THEN** the result SHALL equal the original input string

### Requirement: UTC epoch to local datetime string conversion
The system SHALL provide an `epochToLocalDatetime` function that converts a UTC epoch timestamp in seconds to an HTML `datetime-local` format string (`YYYY-MM-DDTHH:mm`) in the browser's local timezone. This is used to pre-fill `datetime-local` inputs from API data.

#### Scenario: Convert epoch to datetime-local string
- **WHEN** `epochToLocalDatetime(1705305600)` is called in a browser at UTC+0
- **THEN** the function returns `"2024-01-15T08:00"`

#### Scenario: Pad single-digit values
- **WHEN** `epochToLocalDatetime` is called with an epoch that resolves to month 3, day 5, hour 9, minute 7
- **THEN** the returned string SHALL have zero-padded values: `"YYYY-03-05T09:07"`

### Requirement: UTC epoch to local display time conversion
The system SHALL provide an `epochToDisplayTime` function that converts a UTC epoch timestamp in seconds to a 24-hour format time string (`HH:MM:SS`) in the browser's local timezone. This is the primary display format for all time values.

#### Scenario: Format epoch as display time
- **WHEN** `epochToDisplayTime(1705305600)` is called in a browser at UTC+0
- **THEN** the function returns `"08:00:00"`

#### Scenario: Return em dash for falsy input
- **WHEN** `epochToDisplayTime(0)` or `epochToDisplayTime(null)` is called
- **THEN** the function returns `"—"` (em dash)

#### Scenario: Pad single-digit time components
- **WHEN** the epoch resolves to hour 1, minute 5, second 3 in local time
- **THEN** the function returns `"01:05:03"`

### Requirement: EpochTimePipe delegates to TimeUtils
The `EpochTimePipe` SHALL delegate its formatting to `epochToDisplayTime` from `TimeUtils`. The pipe's public API (`transform(value: number): string`) SHALL remain unchanged.

#### Scenario: Pipe produces same output as epochToDisplayTime
- **WHEN** `EpochTimePipe.transform(epoch)` is called
- **THEN** the result SHALL equal `epochToDisplayTime(epoch)`

### Requirement: Route editor uses TimeUtils for time conversion
The `RouteEditorComponent` SHALL use `localDatetimeToEpoch` when converting the start time input to an epoch for the API request, and `epochToLocalDatetime` when pre-filling the start time input from existing timetable data. The inline `formatTime()` method SHALL be removed and replaced by the `epochTime` pipe in the template.

#### Scenario: Submit converts start time via TimeUtils
- **WHEN** the user submits a route update with start time "2024-01-15T08:00"
- **THEN** the emitted `start_time` value SHALL equal `localDatetimeToEpoch("2024-01-15T08:00")`

#### Scenario: Initial state pre-fills start time via TimeUtils
- **WHEN** the component loads with existing timetable data (first entry arrival = epoch X)
- **THEN** the `startTimeLocal` signal SHALL be set to `epochToLocalDatetime(X)`

#### Scenario: Timetable display uses epochTime pipe
- **WHEN** timetable arrival and departure times are rendered
- **THEN** they SHALL use the `epochTime` pipe (not an inline `formatTime()` method)

### Requirement: Conflict alert uses EpochTimePipe for time display
The `ConflictAlertComponent` SHALL use the `epochTime` pipe for formatting `overlap_start` and `overlap_end` values. The inline `formatTime()` method SHALL be removed.

#### Scenario: Block conflict overlap times use pipe
- **WHEN** a block conflict with `overlap_start` and `overlap_end` is displayed
- **THEN** both times SHALL be formatted via the `epochTime` pipe

#### Scenario: Interlocking conflict overlap times use pipe
- **WHEN** an interlocking conflict with `overlap_start` and `overlap_end` is displayed
- **THEN** both times SHALL be formatted via the `epochTime` pipe

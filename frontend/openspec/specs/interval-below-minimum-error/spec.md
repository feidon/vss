### Requirement: INTERVAL_BELOW_MINIMUM error formatter
The frontend `ERROR_FORMATTERS` SHALL include an entry for the `INTERVAL_BELOW_MINIMUM` error code that renders a user-friendly message containing the requested interval and the minimum achievable interval from the error context.

#### Scenario: Error with valid context fields
- **WHEN** the backend returns a 400 response with `error_code: "INTERVAL_BELOW_MINIMUM"` and context `{ "requested_interval": 59, "minimum_interval": 60, "dwell_time": 15, "min_departure_gap": 75 }`
- **THEN** `extractErrorMessage` SHALL return `"Interval 59s is below the minimum of 60s due to interlocking constraints."`

#### Scenario: Error with missing context fields
- **WHEN** the backend returns `error_code: "INTERVAL_BELOW_MINIMUM"` but the context is missing `requested_interval` or `minimum_interval`
- **THEN** the formatter SHALL return `null`, causing `extractErrorMessage` to fall through to the provided fallback message

#### Scenario: Auto-schedule dialog displays the formatted message
- **WHEN** a user submits the auto-schedule form with an interval below the track's minimum
- **THEN** the dialog SHALL display the formatted error message (not the generic fallback)

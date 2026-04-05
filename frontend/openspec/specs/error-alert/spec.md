### Requirement: Shared error alert component
The system SHALL provide a shared `ErrorAlertComponent` (`app-error-alert`) that displays an error message string with a dismiss action. The component SHALL accept a required `message` string input and emit a `dismiss` output event.

#### Scenario: Error alert renders message
- **WHEN** the component receives a `message` input of "Failed to load vehicles"
- **THEN** it SHALL display "Failed to load vehicles" in a red-bordered alert box

#### Scenario: Error alert dismiss button
- **WHEN** the user clicks the `×` button on the error alert
- **THEN** the component SHALL emit a `dismiss` event

#### Scenario: Visual consistency with conflict alert
- **WHEN** the error alert is rendered
- **THEN** it SHALL use the same visual pattern as `ConflictAlertComponent`: red border, red background tint, `×` close button positioned in the top-right corner

### Requirement: Extract error message from HTTP responses
The system SHALL provide an `extractErrorMessage` utility function that extracts a user-facing message from an `HttpErrorResponse`. The function SHALL accept the error and a fallback string.

#### Scenario: Server error returns constant message
- **WHEN** the HTTP response has status >= 500
- **THEN** the function SHALL return "Something went wrong. Please try again later." regardless of the response body

#### Scenario: 422 with string detail
- **WHEN** the HTTP response has status 422 and `error.detail` is a string (e.g., "Start time must be in the future")
- **THEN** the function SHALL return that string as the error message

#### Scenario: 4xx with object detail containing message
- **WHEN** the HTTP response has status 4xx and `error.detail` is an object with a `message` string field
- **THEN** the function SHALL return the `message` string

#### Scenario: Unrecognized error format
- **WHEN** the HTTP response has no parseable `detail` field and status < 500
- **THEN** the function SHALL return the provided fallback string

### Requirement: Schedule editor uses shared error alert
The `ScheduleEditorComponent` SHALL replace its inline error message markup with the shared `ErrorAlertComponent`. On non-409 errors from route updates, it SHALL use `extractErrorMessage` to derive the displayed message.

#### Scenario: 422 validation error on route update
- **WHEN** a route update returns HTTP 422 with `detail: "Route must contain at least two stops"`
- **THEN** the schedule editor SHALL display "Route must contain at least two stops" in the error alert

#### Scenario: 500 error on route update
- **WHEN** a route update returns HTTP 500
- **THEN** the schedule editor SHALL display "Something went wrong. Please try again later."

#### Scenario: Error alert dismiss in schedule editor
- **WHEN** the user dismisses the error alert in the schedule editor
- **THEN** the error message signal SHALL be set to null, hiding the alert

### Requirement: Schedule list error handling
The `ScheduleListComponent` SHALL handle errors from service list loading, service deletion, and service detail fetching. Errors SHALL be displayed using the shared `ErrorAlertComponent` at the top of the list.

#### Scenario: Service list load fails
- **WHEN** loading the service list returns an HTTP error
- **THEN** the component SHALL display an error message derived via `extractErrorMessage` with fallback "Failed to load services"

#### Scenario: Service delete fails
- **WHEN** deleting a service returns an HTTP error
- **THEN** the component SHALL display an error message derived via `extractErrorMessage` with fallback "Failed to delete service"

#### Scenario: Service detail fetch fails
- **WHEN** fetching a service detail for the expanded row returns an HTTP error
- **THEN** the component SHALL display an error message derived via `extractErrorMessage` with fallback "Failed to load service details"

#### Scenario: Error is dismissible
- **WHEN** the user dismisses the error alert in the schedule list
- **THEN** the error message SHALL be cleared

### Requirement: Block config uses shared error alert
The `BlockConfigComponent` SHALL replace its plain red text error display with the shared `ErrorAlertComponent`, making errors dismissible.

#### Scenario: Block load error is dismissible
- **WHEN** loading blocks fails and the error alert is shown
- **THEN** the user SHALL be able to dismiss the error via the `×` button

#### Scenario: Block update error is dismissible
- **WHEN** updating a block fails and the error alert is shown
- **THEN** the user SHALL be able to dismiss the error via the `×` button

### Requirement: Create service dialog error handling
The `CreateServiceDialogComponent` SHALL display errors from service creation using `extractErrorMessage` and a visible error message, replacing the current silent failure.

#### Scenario: Service creation fails with 422
- **WHEN** creating a service returns HTTP 422 with `detail: "Service name already exists"`
- **THEN** the dialog SHALL display "Service name already exists" as an error message

#### Scenario: Service creation fails with 500
- **WHEN** creating a service returns HTTP 500
- **THEN** the dialog SHALL display "Something went wrong. Please try again later."

#### Scenario: Service creation error resets saving state
- **WHEN** creating a service returns any HTTP error
- **THEN** the dialog SHALL reset the saving state to allow retry

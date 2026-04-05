## MODIFIED Requirements

### Requirement: Error alert displays messages from error responses

The `ErrorAlertComponent` SHALL continue to accept a `message` string input and display it. No changes to the component itself — the richer messages are produced upstream by `extractErrorMessage` with name substitution.

#### Scenario: Structured error message displayed
- **WHEN** the component receives a message that was produced by `extractErrorMessage` with name-resolved context (e.g., "Stop P1A not found")
- **THEN** the component SHALL display the message as-is

#### Scenario: Fallback message displayed
- **WHEN** the component receives a fallback message (e.g., "Failed to update route. Please try again.")
- **THEN** the component SHALL display the fallback message as-is

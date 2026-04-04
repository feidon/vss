### Requirement: Back link is positioned above the service title
The back navigation link SHALL be rendered on its own line above the service name heading, not inline with it.

#### Scenario: Visual layout
- **WHEN** the schedule editor page loads for a service
- **THEN** the "← Back to Schedule" link appears above the service name heading as a separate element

### Requirement: Back link uses subtle text styling
The back link SHALL be styled as a small, muted text link rather than a prominent button.

#### Scenario: Link appearance
- **WHEN** the schedule editor page is displayed
- **THEN** the back link uses small text size with muted gray color (not a button with background)

#### Scenario: Hover feedback
- **WHEN** the user hovers over the back link
- **THEN** the text color darkens to indicate interactivity

### Requirement: Service name has primary visual prominence
The service name heading SHALL be the most visually dominant element in the header area.

#### Scenario: Heading prominence
- **WHEN** the schedule editor page loads
- **THEN** the service name is displayed as a large, bold heading below the back link

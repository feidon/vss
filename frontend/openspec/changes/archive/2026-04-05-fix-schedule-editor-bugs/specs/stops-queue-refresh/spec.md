## ADDED Requirements

### Requirement: Stops queue resets from API data on service input change
The route editor SHALL reset its stops queue to match only the stops from the API response whenever the `service` input signal changes. Manually-added stops from a previous session MUST NOT persist.

#### Scenario: Page refresh clears manually-added stops
- **WHEN** a user adds stops manually to the queue, then refreshes the page
- **THEN** the stops queue SHALL contain only the stops returned by the API for that service

#### Scenario: Service input changes after navigation
- **WHEN** the parent component sets a new `service` value (e.g., navigating to a different service)
- **THEN** the stops queue SHALL be re-derived entirely from the new service's route data

#### Scenario: Initial load populates stops from API
- **WHEN** the route editor component is first created with a service input
- **THEN** the stops queue SHALL be populated from the service's route data (same as current behavior)

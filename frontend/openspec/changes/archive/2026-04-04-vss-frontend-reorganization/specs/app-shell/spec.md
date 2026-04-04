## MODIFIED Requirements

### Requirement: Navigation bar
The app shell SHALL display a navigation bar with links to: Schedule (`/schedule`) and Config (`/config`). The active route link SHALL be visually distinguished. Links to `/editor`, `/viewer`, `/blocks`, and `/map` are removed.

#### Scenario: Navigation renders all links
- **WHEN** the app loads
- **THEN** the nav bar displays two links: Schedule, Config

#### Scenario: Active route highlighting
- **WHEN** the user is on `/schedule`
- **THEN** the Schedule nav link is visually highlighted as active

#### Scenario: Child route highlighting
- **WHEN** the user is on `/schedule/101/edit`
- **THEN** the Schedule nav link is still visually highlighted as active

### Requirement: Lazy-loaded feature routes
The app SHALL define routes that lazy-load each feature component:
- `/schedule` → `ScheduleListComponent` (with child route `/:id/edit` → `ScheduleEditorComponent`)
- `/config` → `ConfigComponent` (with block config and track map overview)

The default route (`/`) SHALL redirect to `/schedule`.

#### Scenario: Default redirect
- **WHEN** user navigates to `/`
- **THEN** they are redirected to `/schedule`

#### Scenario: Lazy loading
- **WHEN** user navigates to `/config` for the first time
- **THEN** the config feature chunk is loaded on demand

#### Scenario: Child route navigation
- **WHEN** user navigates to `/schedule/101/edit`
- **THEN** the `ScheduleEditorComponent` renders within the schedule route's router outlet

### Requirement: Router outlet in shell
The app component SHALL contain a `<router-outlet>` that renders the active feature component below the navigation bar.

#### Scenario: Route content rendering
- **WHEN** user clicks the "Config" nav link
- **THEN** the `ConfigComponent` renders in the router outlet area

## REMOVED Requirements

### Requirement: Placeholder feature components
**Reason**: All feature components are now real implementations; placeholders are no longer needed.
**Migration**: Remove placeholder components; each route renders its actual feature component.

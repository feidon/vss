## ADDED Requirements

### Requirement: Navigation bar
The app shell SHALL display a navigation bar with links to: Editor (`/editor`), Viewer (`/viewer`), Blocks (`/blocks`), Map (`/map`). The active route link SHALL be visually distinguished.

#### Scenario: Navigation renders all links
- **WHEN** the app loads
- **THEN** the nav bar displays four links: Editor, Viewer, Blocks, Map

#### Scenario: Active route highlighting
- **WHEN** the user is on `/editor`
- **THEN** the Editor nav link is visually highlighted as active

### Requirement: Lazy-loaded feature routes
The app SHALL define routes that lazy-load each feature component:
- `/editor` → `ScheduleEditorComponent`
- `/viewer` → `ScheduleViewerComponent`
- `/blocks` → `BlockConfigComponent`
- `/map` → `TrackMapComponent`

The default route (`/`) SHALL redirect to `/editor`.

#### Scenario: Default redirect
- **WHEN** user navigates to `/`
- **THEN** they are redirected to `/editor`

#### Scenario: Lazy loading
- **WHEN** user navigates to `/blocks` for the first time
- **THEN** the `BlockConfigComponent` chunk is loaded on demand

### Requirement: Placeholder feature components
Each feature route SHALL render a placeholder standalone component with the feature name displayed. These placeholders will be replaced by real implementations in subsequent changes.

#### Scenario: Placeholder content
- **WHEN** user navigates to `/viewer`
- **THEN** the page displays "Schedule Viewer" as placeholder text

### Requirement: Router outlet in shell
The app component SHALL contain a `<router-outlet>` that renders the active feature component below the navigation bar.

#### Scenario: Route content rendering
- **WHEN** user clicks the "Blocks" nav link
- **THEN** the `BlockConfigComponent` renders in the router outlet area

## ADDED Requirements

### Requirement: Row click toggles expansion

Clicking anywhere on a service row (except action buttons) SHALL toggle an expansion panel beneath that row. Only one row SHALL be expanded at a time — expanding a different row collapses the previously expanded one.

#### Scenario: Expand a collapsed row
- **WHEN** user clicks on a collapsed service row
- **THEN** an expansion panel appears beneath the row showing the route path

#### Scenario: Collapse an expanded row
- **WHEN** user clicks on the currently expanded service row
- **THEN** the expansion panel is removed

#### Scenario: Expand a different row while one is already expanded
- **WHEN** user clicks on a different service row while another is expanded
- **THEN** the previously expanded row collapses and the clicked row expands

#### Scenario: Edit button does not trigger expansion
- **WHEN** user clicks the Edit button on a service row
- **THEN** the router navigates to the editor without toggling expansion

#### Scenario: Delete button does not trigger expansion
- **WHEN** user clicks the Delete button on a service row
- **THEN** the delete confirmation appears without toggling expansion

### Requirement: Expansion panel displays route path

The expansion panel SHALL display the full route as a chain of node names joined by ` → ` (e.g., `Y → B1 → B3 → P2A`). All node types (yard, block, platform) SHALL be included.

#### Scenario: Service with a defined route
- **WHEN** the expansion panel is shown for a service that has a route
- **THEN** the panel displays all node names from the route array joined by ` → `

#### Scenario: Service with no route
- **WHEN** the expansion panel is shown for a service with an empty route
- **THEN** the panel displays "No route defined"

### Requirement: Lazy-fetch and cache service detail

The service detail (`GET /api/services/{id}`) SHALL be fetched only on the first expansion of a row. Subsequent expand/collapse toggles SHALL use the cached response without re-fetching.

#### Scenario: First expansion fetches detail
- **WHEN** a row is expanded for the first time
- **THEN** the system calls `GET /api/services/{id}` and caches the response

#### Scenario: Subsequent expansion uses cache
- **WHEN** a previously expanded row is collapsed and re-expanded
- **THEN** the system uses the cached detail without making an API call

#### Scenario: Loading state during fetch
- **WHEN** a row is expanded and the detail is being fetched
- **THEN** the expansion panel displays "Loading..." until the response arrives

#### Scenario: Cache is cleared on list refresh
- **WHEN** the service list is refreshed (e.g., after a delete)
- **THEN** the detail cache is cleared so stale data is not shown

### Requirement: Expanded row visual styling

The expansion panel SHALL be visually distinct from the regular table rows so the user can clearly see which row is expanded and where the route information is.

#### Scenario: Expanded row styling
- **WHEN** a row is expanded
- **THEN** the expansion panel has a light background (e.g., `bg-gray-50`) and the route text is displayed in a smaller, muted font

#### Scenario: Cursor indicates clickability
- **WHEN** user hovers over a service row
- **THEN** the cursor changes to pointer to indicate the row is clickable

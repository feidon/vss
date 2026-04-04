## Context

The VSS frontend currently has 4 top-level routes (Editor, Viewer, Blocks, Map) served by separate feature directories. The Editor page contains both the service list and route editor as a view-mode toggle. The Viewer page duplicates the service list with read-only timetable display. The Track Map page is an empty placeholder. This fragmentation means users bounce between tabs for related tasks.

Current component structure:
- `schedule-editor/` — ServiceFormComponent, ServiceListComponent, RouteEditorComponent, ConflictAlertComponent
- `schedule-viewer/` — ViewerServiceListComponent, TimetableDetailComponent
- `block-config/` — BlockConfigComponent (standalone)
- `track-map/` — TrackMapComponent (empty placeholder)

## Goals / Non-Goals

**Goals:**
- Consolidate navigation to 2 pages: Schedule (list + editor) and Config (blocks + track overview)
- Make service creation a dialog that collects name, vehicle, and start time upfront
- Use Angular child routes so the editor is a sub-page of the schedule list
- Introduce the track map as the primary route-building interface in the editor

**Non-Goals:**
- No backend API changes
- No new conflict detection logic
- No changes to block-config editing behavior (just relocated)
- No drag-and-drop or advanced map interactions beyond click-to-select

## Decisions

### 1. Route structure: flat → nested child routes

**Choice:** Replace 4 flat routes with 2 parent routes, each with child routes.

```
/schedule              → ScheduleListComponent (service list)
/schedule/:id/edit     → ScheduleEditorComponent (route editor with track map)
/config                → ConfigComponent (block config + track overview)
```

Default redirect: `/` → `/schedule`.

**Why over alternatives:**
- *Tab parameters (`/schedule?mode=edit`)*: Doesn't preserve browser history for back navigation; can't deep-link to a specific service editor.
- *Separate top-level routes (`/editor/:id`)*: Loses the parent-child relationship; nav bar highlighting breaks.

Child routes use `<router-outlet>` within the schedule parent component for clean transitions.

### 2. Feature directory consolidation

**Choice:** Merge `schedule-editor/` and `schedule-viewer/` into a single `schedule/` feature directory. Merge `block-config/` and `track-map/` into `config/`.

```
features/
├── schedule/
│   ├── schedule-list.ts        # Service list (was viewer-service-list + service-list)
│   ├── schedule-editor.ts      # Route editor shell (child route)
│   ├── create-service-dialog.ts # Modal dialog
│   ├── route-editor.ts         # Stop queue + timetable (reused from editor)
│   ├── track-map-editor.ts     # d3.js map for route building
│   └── conflict-alert.ts       # Conflict display (moved)
└── config/
    ├── config.ts               # Parent with tabs/sections
    ├── block-config.ts          # Block editing (moved as-is)
    └── track-map-overview.ts    # Read-only track visualization
```

**Why:** One feature = one directory. Avoids cross-feature imports and keeps lazy-loading boundaries clean.

### 3. Create-service dialog: Angular CDK Dialog

**Choice:** Use `@angular/cdk/dialog` for the create-service modal. The dialog collects name, vehicle (dropdown), and start time (datetime-local input) in one step. On submit, it calls `POST /services` and returns the new service ID.

**Why over alternatives:**
- *Inline form (current approach)*: Doesn't visually separate creation from the list; start time was a separate concern in the route editor.
- *Separate route (`/schedule/new`)*: Over-engineered for a 3-field form; modal is more natural UX.
- *Third-party dialog lib*: CDK Dialog is already part of Angular's ecosystem, zero extra dependencies.

### 4. Track map editor: d3.js click-to-select

**Choice:** The route editor embeds a d3.js track map (using the existing graph data from `GET /api/services/{id}`). Platforms and yards are clickable nodes. Clicking a platform/yard adds it to the stop queue. The stop queue panel sits beside the map showing the ordered stops with dwell time inputs.

**Why:** The track map makes the network topology visible while building routes, replacing the abstract dropdown-based stop picker. Users see which platforms are reachable and understand the route geometry.

**Data flow:**
1. Load graph via service detail response (already includes nodes, connections, stations)
2. Render nodes at their `(x, y)` positions using d3
3. Highlight clickable nodes (platforms + yards) vs non-clickable (blocks)
4. On click → append to stop queue signal → update dwell time → user can reorder/remove
5. On save → call `PATCH /services/{id}/route` with stops + start_time

### 5. Schedule list: unified from two components

**Choice:** A single `ScheduleListComponent` replaces both `ServiceListComponent` (from editor) and `ViewerServiceListComponent` (from viewer). It combines the vehicle filter from viewer with the create/edit/delete actions from editor.

**Why:** The two components displayed the same data with different action sets. Unifying avoids duplication and gives users all capabilities in one place.

## Risks / Trade-offs

- **d3.js complexity in editor** — The track map editor is more complex than the current dropdown picker. Risk: interactions may be unfamiliar to users. → Mitigation: Keep the stop queue panel visible as a fallback reference; platforms highlight on hover with name tooltips.

- **CDK Dialog dependency** — Adds `@angular/cdk` as a dependency. → Mitigation: CDK is maintained by the Angular team and already compatible; it's a peer dependency of Angular Material which many projects use. Lightweight compared to full Material.

- **Migration disruption** — Reorganizing feature directories changes all import paths. → Mitigation: Single atomic change; no incremental migration needed since the app is small. Old routes (`/editor`, `/viewer`) will be removed (no redirects needed for a single-user app).

- **Track map not yet implemented** — The current track-map component is empty. → Mitigation: The graph data (nodes with x,y coordinates, connections) is already available from the API. d3 rendering is additive.

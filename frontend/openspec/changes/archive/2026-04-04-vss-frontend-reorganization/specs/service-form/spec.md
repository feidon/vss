## REMOVED Requirements

### Requirement: Create a new service
**Reason**: Replaced by the `create-service-dialog` capability. The inline form is replaced by a modal dialog that also collects start time upfront.
**Migration**: Use `CreateServiceDialogComponent` opened from the schedule list's "Create Service" button.

### Requirement: Edit service route with platform stops
**Reason**: The stop picker UI is replaced by the `track-map-editor` capability where users click platforms/yards on the map. The underlying route update API call (`PATCH /services/{id}/route`) remains the same.
**Migration**: Use `TrackMapEditorComponent` with the stop queue panel for route building. Dwell time editing and start time are preserved in the new UI.

### Requirement: Display current timetable after route update
**Reason**: Timetable display is retained in the editor but is now part of the `ScheduleEditorComponent` which uses the track-map-based workflow.
**Migration**: Timetable rendering logic moves to the schedule editor component.

### Requirement: Back to list navigation
**Reason**: Back navigation is now handled by Angular router (navigating from `/schedule/:id/edit` back to `/schedule`). No custom view-mode toggle needed.
**Migration**: Use `routerLink="/schedule"` or browser back button.

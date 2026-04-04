## MODIFIED Requirements

### Requirement: Editor populates stop queue from existing service route
When the user navigates to the editor for a service that already has a saved route, the stop queue SHALL be populated with the non-block nodes from the route, each with its correct dwell time derived from the timetable. Block nodes (type `'block'`) SHALL be excluded from the stop queue. The filter SHALL apply both to the stop list UI and to the queued node IDs emitted to the track map.

#### Scenario: Existing service with saved route
- **WHEN** user navigates to `/schedule/:id/edit` for a service with route `[P1A, B3, B5, P2A]` and timetable entries for each node
- **THEN** the stop queue displays `[P1A, P2A]` (blocks filtered out), each with dwell time = `departure - arrival` from the corresponding timetable entry

#### Scenario: Existing service with no route
- **WHEN** user navigates to `/schedule/:id/edit` for a service with an empty route
- **THEN** the stop queue is empty and the start time field is blank

#### Scenario: Track map only highlights non-block queued nodes
- **WHEN** user navigates to `/schedule/:id/edit` for a service with route `[P1A, B3, B5, P2A]`
- **THEN** only P1A and P2A are highlighted on the track map as queued stops; B3 and B5 are not highlighted

#### Scenario: Route update refreshes stop queue without blocks
- **WHEN** user submits a route update and the service is refetched with route `[Y, B1, P1A, B3, P2A]`
- **THEN** the stop queue displays `[Y, P1A, P2A]` (blocks filtered out)

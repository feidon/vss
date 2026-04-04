## MODIFIED Requirements

### Requirement: Display timetable entries in order
The system SHALL display the timetable of a selected service as an ordered table with columns: order, node name, node type, arrival time, and departure time. Node names SHALL be resolved by searching the service route array first (which includes block nodes), then graph edges, then displaying the raw node ID as a fallback. The `Node` type union SHALL include `BlockNode` (type: `'block'`) so block nodes from the API response are properly typed.

#### Scenario: Service with timetable entries
- **WHEN** the user selects a service that has timetable entries
- **THEN** the system displays each timetable entry sorted by `order`, showing the node name resolved from the service route or graph edges, the node type (block/platform/yard), and the arrival and departure times

#### Scenario: Service with no timetable entries
- **WHEN** the user selects a service that has an empty timetable
- **THEN** the system displays a message indicating the service has no timetable (route not yet configured)

#### Scenario: Timetable entry references a block node
- **WHEN** a timetable entry has a `node_id` that corresponds to a block (type `'block'`) in the service route
- **THEN** the system displays the block's name (e.g., "B1", "B13") and type "block" — never a raw UUID

#### Scenario: Timetable entry references a node not in route
- **WHEN** a timetable entry has a `node_id` that is not found in the service route array
- **THEN** the system searches graph edges by ID, and if found, displays the edge name; otherwise displays the raw node ID

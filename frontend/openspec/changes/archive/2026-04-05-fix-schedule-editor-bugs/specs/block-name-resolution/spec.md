## ADDED Requirements

### Requirement: Conflict alert resolves block names from graph edges
The conflict alert component SHALL resolve block node names by looking up IDs in both `graph.nodes` and `graph.edges`. Block IDs that appear in conflict responses MUST display the edge's human-readable name, not the raw UUID.

#### Scenario: Block conflict displays block name
- **WHEN** a block conflict references a `block_id` that exists in `graph.edges`
- **THEN** the conflict alert SHALL display the edge's `name` property (e.g., "B3") instead of the UUID

#### Scenario: Interlocking conflict displays block names
- **WHEN** an interlocking conflict references `block_a_id` and `block_b_id`
- **THEN** the conflict alert SHALL display each block's human-readable name from `graph.edges`

#### Scenario: Node names still resolve for platforms and yards
- **WHEN** a conflict references a node ID that exists in `graph.nodes`
- **THEN** the conflict alert SHALL continue to display the node's name as before (no regression)

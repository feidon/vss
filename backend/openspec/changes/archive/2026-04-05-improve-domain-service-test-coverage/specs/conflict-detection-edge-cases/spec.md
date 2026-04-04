## ADDED Requirements

### Requirement: Vehicle conflict detection with single service
When only one service exists for a vehicle, there SHALL be no vehicle conflicts.

#### Scenario: Single service no conflicts
- **WHEN** `detect_conflicts` is called with a single candidate service and no other services
- **THEN** `vehicle_conflicts` SHALL be empty

### Requirement: Vehicle conflict detection with multiple location discontinuities
When multiple consecutive services have location gaps, all discontinuities SHALL be detected.

#### Scenario: Three services with two discontinuities
- **WHEN** three sequential services end/start at different locations (A->B, C->D, E->F where B!=C and D!=E)
- **THEN** `vehicle_conflicts` SHALL contain 2 location discontinuity conflicts

### Requirement: Vehicle conflict detection detects both overlap and discontinuity
When two services both overlap in time AND have a location gap, both conflict types SHALL be reported.

#### Scenario: Overlapping time windows with location discontinuity
- **WHEN** two services for the same vehicle overlap in time AND start/end at different nodes
- **THEN** `vehicle_conflicts` SHALL contain both an "Overlapping time windows" and a "Location discontinuity" conflict

### Requirement: Interlocking same-block overlap is not reported
When two services occupy the SAME block in the same interlocking group at overlapping times, it SHALL NOT be reported as an interlocking conflict (it is already a block conflict).

#### Scenario: Same block same group overlap
- **WHEN** two services occupy the same block (group 1) at overlapping times
- **THEN** `interlocking_conflicts` SHALL be empty (the overlap is caught by block conflict detection instead)

### Requirement: Interlocking different groups no conflict
When two services occupy blocks in different interlocking groups at overlapping times, no interlocking conflict SHALL be reported.

#### Scenario: Different groups overlapping
- **WHEN** service A occupies block in group 1 and service B occupies block in group 2 at overlapping times
- **THEN** `interlocking_conflicts` SHALL be empty

### Requirement: Interlocking detects multiple group conflicts
When multiple interlocking groups have conflicts simultaneously, all SHALL be detected.

#### Scenario: Conflicts in two groups simultaneously
- **WHEN** services overlap in both group 1 (different blocks) and group 2 (different blocks)
- **THEN** `interlocking_conflicts` SHALL contain conflicts for both groups

### Requirement: Block conflict detection across multiple blocks
When services conflict on multiple different blocks, all block conflicts SHALL be detected.

#### Scenario: Two different blocks with overlapping occupancy
- **WHEN** two services each occupy two blocks, and both blocks have overlapping times
- **THEN** `block_conflicts` SHALL contain one conflict per overlapping block

### Requirement: Block conflict touching boundary not reported
When one service's departure on a block exactly equals another service's arrival, it SHALL NOT be a conflict.

#### Scenario: Touching boundary on same block
- **WHEN** service A departs block at t=100 and service B arrives at the same block at t=100
- **THEN** `block_conflicts` SHALL be empty

### Requirement: Battery detection with empty steps
When there are no battery simulation steps (e.g., service has only platform nodes), no battery conflict SHALL be reported.

#### Scenario: Empty battery steps
- **WHEN** `detect_battery_conflicts` is called with an empty steps list
- **THEN** the result SHALL be an empty list

### Requirement: Battery detection single block traversal
A single block traversal from full battery SHALL never trigger a conflict.

#### Scenario: Single block from full battery
- **WHEN** a vehicle at 80% traverses exactly 1 block
- **THEN** battery is 79% which is above critical (30%), so no conflict SHALL be reported

### Requirement: Battery detection exactly at critical after traversal
When battery drops to exactly 30% after a traversal, it SHALL NOT be reported as critical (critical is < 30).

#### Scenario: Battery at exactly 30 after traversal
- **WHEN** a vehicle starts at 80% and traverses 50 blocks (80-50=30)
- **THEN** no LOWBATTERY conflict SHALL be reported (30 is not < 30)

### Requirement: ServiceConflicts has_conflicts property
`has_conflicts` SHALL return True when any conflict list is non-empty, and False when all are empty.

#### Scenario: Only block conflicts present
- **WHEN** ServiceConflicts has non-empty `block_conflicts` but all others empty
- **THEN** `has_conflicts` SHALL be True

#### Scenario: Only interlocking conflicts present
- **WHEN** ServiceConflicts has non-empty `interlocking_conflicts` but all others empty
- **THEN** `has_conflicts` SHALL be True

#### Scenario: All empty
- **WHEN** ServiceConflicts has all empty conflict lists
- **THEN** `has_conflicts` SHALL be False

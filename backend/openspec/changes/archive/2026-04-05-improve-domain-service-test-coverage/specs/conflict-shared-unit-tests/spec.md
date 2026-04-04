## ADDED Requirements

### Requirement: find_time_overlaps returns empty for no entries
`find_time_overlaps` SHALL return an empty list when given an empty input list.

#### Scenario: Empty input
- **WHEN** `find_time_overlaps` is called with `entries=[]`
- **THEN** the result SHALL be `[]`

### Requirement: find_time_overlaps returns empty for single entry
`find_time_overlaps` SHALL return an empty list when given exactly one entry.

#### Scenario: Single entry
- **WHEN** `find_time_overlaps` is called with one entry `[BlockOccupancy(1, 0, 10)]`
- **THEN** the result SHALL be `[]`

### Requirement: find_time_overlaps detects overlapping pair
`find_time_overlaps` SHALL detect when two entries have overlapping time windows.

#### Scenario: Two overlapping entries
- **WHEN** `find_time_overlaps` is called with entries `[(0,15), (10,20)]`
- **THEN** the result SHALL contain exactly one pair

### Requirement: find_time_overlaps respects touching boundaries
`find_time_overlaps` SHALL NOT report a conflict when one entry's departure equals another's arrival (touching but not overlapping).

#### Scenario: Touching boundaries
- **WHEN** `find_time_overlaps` is called with entries `[(0,10), (10,20)]`
- **THEN** the result SHALL be `[]`

### Requirement: find_time_overlaps handles unsorted input
`find_time_overlaps` SHALL correctly detect overlaps regardless of input order.

#### Scenario: Reverse-ordered input
- **WHEN** `find_time_overlaps` is called with entries in reverse arrival order `[(10,20), (0,15)]`
- **THEN** the result SHALL still detect the overlap

### Requirement: find_time_overlaps detects multiple overlapping pairs
`find_time_overlaps` SHALL detect all pairwise overlaps in a list of entries.

#### Scenario: Three mutually overlapping entries
- **WHEN** `find_time_overlaps` is called with entries `[(0,20), (5,15), (10,25)]`
- **THEN** the result SHALL contain 3 pairs: (first, second), (first, third), (second, third)

### Requirement: build_vehicle_schedule returns empty for no matching services
`build_vehicle_schedule` SHALL return empty windows and endpoints when no services match the vehicle ID.

#### Scenario: No matching vehicle
- **WHEN** `build_vehicle_schedule` is called with a vehicle ID that matches none of the provided services
- **THEN** the result SHALL have empty `windows` and empty `endpoints`

### Requirement: build_vehicle_schedule sorts by start time
`build_vehicle_schedule` SHALL return windows and endpoints sorted by start time.

#### Scenario: Multiple services out of order
- **WHEN** `build_vehicle_schedule` is called with two services where the second has an earlier start time
- **THEN** the result's `windows` and `endpoints` SHALL be sorted ascending by start

### Requirement: build_occupancies skips platform entries
`build_occupancies` SHALL only create occupancies for block nodes, skipping platform and yard entries.

#### Scenario: Mixed block and platform entries
- **WHEN** `build_occupancies` is called with a service that has both block and platform timetable entries
- **THEN** the `by_block` dict SHALL contain only block entries
- **AND** the `by_group` dict SHALL contain only block entries

### Requirement: build_occupancies returns empty for no services
`build_occupancies` SHALL return empty dicts when no services are provided.

#### Scenario: Empty services list
- **WHEN** `build_occupancies` is called with `services=[]` and `blocks=[]`
- **THEN** both returned dicts SHALL be empty

### Requirement: build_occupancies groups by interlocking group
`build_occupancies` SHALL correctly group occupancies by block's interlocking group number.

#### Scenario: Two blocks in different groups
- **WHEN** `build_occupancies` is called with blocks in group 1 and group 2
- **THEN** `by_group[1]` SHALL contain only group-1 block occupancies
- **AND** `by_group[2]` SHALL contain only group-2 block occupancies

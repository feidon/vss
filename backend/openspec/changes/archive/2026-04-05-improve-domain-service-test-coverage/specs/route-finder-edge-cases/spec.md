## ADDED Requirements

### Requirement: RouteFinder handles direct adjacency between platforms
`find_block_chain` SHALL return an empty list when two platforms are directly connected with no intermediate blocks.

#### Scenario: Directly adjacent platforms yield empty block chain
- **WHEN** `find_block_chain` is called with `from_id=P1A` and `to_id=B3` where P1A connects directly to B3 (but B3 is a block, not a platform — so use a synthetic graph where two platforms are directly adjacent)
- **THEN** the result SHALL be an empty list `[]`

### Requirement: RouteFinder finds path through bidirectional blocks
`find_block_chain` SHALL find paths that traverse bidirectional blocks (B1, B2) connecting Yard to platforms.

#### Scenario: Yard to P1A via B1
- **WHEN** `find_block_chain` is called with `from_id=Y` and `to_id=P1A` using the real track network
- **THEN** the result SHALL be `[B1]`

#### Scenario: Yard to P1B via B2
- **WHEN** `find_block_chain` is called with `from_id=Y` and `to_id=P1B` using the real track network
- **THEN** the result SHALL be `[B2]`

#### Scenario: P1A to Yard via B1 (reverse direction)
- **WHEN** `find_block_chain` is called with `from_id=P1A` and `to_id=Y`
- **THEN** the result SHALL be `[B1]` (B1 is bidirectional)

### Requirement: RouteFinder rejects duplicate consecutive stops in build_full_path
`build_full_path` SHALL raise DomainError when two consecutive stops are the same ID.

#### Scenario: Same platform repeated consecutively
- **WHEN** `build_full_path` is called with `stop_ids=[P1A, P1A]`
- **THEN** a DomainError SHALL be raised (no route from P1A to P1A)

### Requirement: RouteFinder builds path starting from Yard
`build_full_path` SHALL correctly build a path that starts at the Yard station.

#### Scenario: Yard to P1A full path
- **WHEN** `build_full_path` is called with `stop_ids=[Y, P1A]`
- **THEN** the result SHALL be `[Y, B1, P1A]`

### Requirement: RouteFinder builds return-to-yard path
`build_full_path` SHALL correctly build a path that ends at the Yard station.

#### Scenario: P1A to Yard full path
- **WHEN** `build_full_path` is called with `stop_ids=[P1A, Y]`
- **THEN** the result SHALL be `[P1A, B1, Y]` (using bidirectional B1)

### Requirement: RouteFinder handles full round trip
`build_full_path` SHALL correctly build a complete round trip starting and ending at Yard.

#### Scenario: Yard round trip via multiple stations
- **WHEN** `build_full_path` is called with `stop_ids=[Y, P1A, P2A, P3A, P2B, P1A, Y]`
- **THEN** the result SHALL include all intermediate blocks in correct order and start/end at Y

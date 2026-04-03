### Requirement: Block update SHALL use pure UPDATE semantics
The `BlockRepository.update()` method SHALL execute a SQL `UPDATE` statement targeting the existing row by primary key. It SHALL NOT insert new rows.

#### Scenario: Update existing block traversal time
- **WHEN** `update()` is called with a block whose ID exists in the database
- **THEN** the corresponding row SHALL be updated with the new field values

#### Scenario: Update non-existent block raises error
- **WHEN** `update()` is called with a block whose ID does not exist in the database
- **THEN** the method SHALL raise a `ValueError`

### Requirement: In-memory fake SHALL match update-only contract
The `InMemoryBlockRepository.update()` method SHALL raise a `ValueError` when called with a block whose ID is not already in the store.

#### Scenario: Fake update of non-existent block
- **WHEN** `update()` is called on `InMemoryBlockRepository` with an unknown block ID
- **THEN** a `ValueError` SHALL be raised

#### Scenario: Fake update of existing block
- **WHEN** `update()` is called on `InMemoryBlockRepository` with a block whose ID exists in the store
- **THEN** the stored block SHALL be replaced with the new value

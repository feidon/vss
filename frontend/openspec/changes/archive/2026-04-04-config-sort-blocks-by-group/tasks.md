## 1. Implementation

- [x] 1.1 Update `groupedBlocks` computed signal in `BlockConfigComponent` to use `localeCompare(b.name, undefined, { numeric: true })` instead of `localeCompare(b.name)`

## 2. Tests

- [x] 2.1 Add/update unit test verifying blocks within Group 2 sort as B3, B4, B13, B14 (not B13, B14, B3, B4)
- [x] 2.2 Add/update unit test verifying blocks within Group 3 sort as B7, B8, B9, B10 (not B10, B7, B8, B9)

## 3. Spec Sync

- [x] 3.1 Update `openspec/specs/block-list/spec.md` sorting scenario to specify natural numeric order instead of alphabetical

## Why

Blocks within each interlocking group are sorted lexicographically by name, causing "B10" to appear before "B2" and "B13" before "B3". This makes the config table hard to scan — users expect natural numeric order (B1, B2, B3, ... B10, B13, B14).

## What Changes

- Switch block sorting within each group from lexicographic (`localeCompare`) to natural numeric order (`localeCompare` with `{ numeric: true }`)
- Update the `block-list` spec to explicitly require natural numeric sorting

## Non-goals

- Changing the group sort order (already correctly sorted by group number)
- Adding user-configurable sort options
- Changing the API response order (sorting is purely client-side)

## Capabilities

### New Capabilities

_(none)_

### Modified Capabilities

- `block-list`: Change sorting requirement from "alphabetically by name" to "natural numeric order by name" so B3 sorts before B13 within the same group

## Impact

- **Component**: `BlockConfigComponent` (`src/app/features/config/block-config.ts`) — one-line change to the `groupedBlocks` computed signal
- **Spec**: `openspec/specs/block-list/spec.md` — update sorting scenario wording
- **Tests**: Update any assertions that depend on block ordering within groups

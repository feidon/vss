## Why

The block configuration page is currently a placeholder stub. Users need to view all 14 blocks with their current traversal times and edit those times to adjust scheduling parameters. This is a core feature required for the assignment.

## What Changes

- Replace the placeholder `BlockConfigComponent` with a fully functional block list and inline editing UI
- Display all blocks grouped by interlocking group, showing name, group, and traversal time
- Allow inline editing of `traversal_time_seconds` per block via PATCH `/blocks/{id}`
- Show success/error feedback after save operations
- Wire up the existing `BlockService` (already implemented in `core/services/block.service.ts`)

## Non-goals

- Bulk editing of multiple blocks simultaneously
- Block creation or deletion (blocks are fixed infrastructure)
- Displaying block relationships on the track map (that's the track-map feature)

## Capabilities

### New Capabilities

- `block-list`: List all blocks with traversal times, grouped by interlocking group, with inline editing and save

### Modified Capabilities

_(none)_

## Impact

- **Components**: `BlockConfigComponent` (rewrite from stub)
- **Services**: `BlockService` (already exists, no changes needed)
- **Models**: `BlockResponse`, `UpdateBlockRequest` (already exist, no changes needed)
- **Routes**: Existing `/blocks` route already points to `BlockConfigComponent`

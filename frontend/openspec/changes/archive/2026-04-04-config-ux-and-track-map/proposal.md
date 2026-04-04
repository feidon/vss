## Why

The block configuration page has several UX issues that hurt usability: blocks render unsorted within groups, the inline edit input is taller than the row causing layout shifts, the edit icon position is inconsistent, and clicking outside the input doesn't save. Additionally, the track map page (`/map`) renders nodes but lacks correct geometry coordinates — the map doesn't visually match the actual railway topology.

## What Changes

- **Block sorting**: Blocks within each interlocking group render sorted by name (e.g., B1 before B2)
- **Stable row height**: The inline edit input field height matches the non-editing row height — no layout shifting when toggling edit mode
- **Edit icon as toggle**: The pencil icon is positioned at a fixed offset to the right of the traversal time value. It remains visible during editing and acts as a toggle — click to open input, click again to close (saving)
- **Click-outside saves**: Clicking anywhere outside an open input field closes it and saves the value to the backend
- **Track map geometry**: Define x,y coordinates for all 14 blocks, 6 platforms, and 1 yard node so the track map renders the correct railway topology (matching the reference layout: S3→S2→S1→Y with upper/lower tracks and crossovers)

## Non-goals

- Changing the block config table structure (columns, grouping logic)
- Adding drag-and-drop or reordering to the block list
- Making the track map editable (geometry is seeded via DB, not user-editable)
- Implementing service highlighting or animation on the track map

## Capabilities

### New Capabilities

- `track-map-geometry`: Define the x,y coordinate layout for all network nodes (blocks, platforms, yard) based on the reference track map image, to be seeded into the database

### Modified Capabilities

- `block-list`: Ensure blocks render sorted by name within each group
- `stable-row-height`: Input field height must match row height — no layout shift on edit toggle
- `click-outside-dismiss`: Clicking outside an open input saves to backend and closes the field; edit icon stays visible during editing and acts as a close/save toggle

## Impact

- **BlockConfigComponent** (`features/config/block-config.ts`): Sorting logic, row height CSS, edit icon positioning, click-outside handling
- **TrackMapEditorComponent** (`features/schedule/track-map-editor.ts`): Will render correctly once geometry is seeded
- **TrackMapOverviewComponent** (`features/config/track-map-overview.ts`): No code changes — benefits from correct geometry automatically
- **Database seed data**: Node x,y coordinates need to be updated (user will handle seeding)
- No API changes required — existing Node response already includes x,y fields

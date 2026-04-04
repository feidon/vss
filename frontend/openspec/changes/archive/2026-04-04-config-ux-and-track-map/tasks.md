## 1. Block Config — Stable Row Height

- [x] 1.1 Set fixed `h-10` on block table rows and remove variable padding (`py-2` → `py-0`) in `block-config.ts` template
- [x] 1.2 Size the inline edit input to `h-8` with compact padding so it fits within the fixed row height
- [x] 1.3 Verify no layout shift when toggling between display and edit modes

## 2. Block Config — Edit Icon as Persistent Toggle

- [x] 2.1 Restructure the traversal time cell: move pencil icon SVG outside the `@if` conditional so it renders in both display and edit modes
- [x] 2.2 Wrap the cell content in a `flex items-center gap-2` container with the value/input on the left and pencil icon button on the right
- [x] 2.3 Add `toggleEdit(block)` method: if currently editing this block → save, otherwise → startEdit
- [x] 2.4 Bind the pencil icon button to `(mousedown.prevent)="toggleEdit(block)"` to prevent blur race condition
- [x] 2.5 Add `aria-label` to the pencil icon button for accessibility

## 3. Block Config — Click Outside Saves

- [x] 3.1 Verify existing `(blur)="onBlur(block)"` fires correctly when clicking outside the input (should already work)
- [x] 3.2 Ensure blur save does not double-fire when pencil icon is clicked (handled by mousedown.prevent in task 2.4)
- [x] 3.3 Confirm that blur with invalid value keeps the input open and shows validation error

## 4. Block Config — Sorting

- [x] 4.1 Verify the `groupedBlocks` computed sorts groups by number and blocks by name within each group
- [x] 4.2 Add a test confirming blocks render in sorted order (B1 before B2 within same group)

## 5. Track Map — Geometry Seed Data

- [x] 5.1 Document the node coordinate reference table (already in spec) for the user to seed into the database
- [x] 5.2 Verify TrackMapOverviewComponent renders correctly once coordinates are seeded (manual test after DB seed)

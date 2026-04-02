## Context

The block configuration page (`BlockConfigComponent`) is currently a placeholder stub with only a heading. The API service (`BlockService`) and models (`BlockResponse`, `UpdateBlockRequest`) already exist. The feature route is already wired up. This change fills in the UI.

There are 14 blocks across 3 interlocking groups. Users need to see all blocks at a glance and adjust traversal times. This is a simple CRUD-lite page (list + inline edit) with no complex state management.

## Goals / Non-Goals

**Goals:**
- Display all blocks with name, group, and traversal time
- Group blocks visually by interlocking group for quick scanning
- Enable inline editing of traversal time per block
- Provide feedback on save success/failure

**Non-Goals:**
- Real-time updates or polling for block changes
- Undo/redo for traversal time edits
- Drag-and-drop or bulk editing

## Decisions

### 1. Single standalone component with signals

**Decision**: Keep the entire block-config feature in one component using Angular signals for state.

**Rationale**: With only 14 blocks and a single editable field, there's no need for a container/presentational split or separate list/detail components. Signals provide clean reactive state without RxJS complexity for this synchronous UI state.

**Alternative considered**: Separate `BlockListComponent` + `BlockEditDialogComponent`. Rejected — a modal/dialog adds UX friction for editing a single number field. Inline editing is simpler and faster.

### 2. Inline editing with input field toggle

**Decision**: Click a traversal time value to switch it to an editable input. Save on blur or Enter, cancel on Escape.

**Rationale**: This pattern is familiar, lightweight, and avoids navigating away from the list. The edit state is tracked per-block via a signal holding the currently-editing block ID.

**Alternative considered**: Always-visible input fields. Rejected — makes the table noisier when the user is just viewing.

### 3. Table layout grouped by interlocking group

**Decision**: Render blocks in a table with visual group separators (group headers). Groups are sorted numerically; blocks within each group are sorted by name.

**Rationale**: The interlocking group is the most meaningful domain grouping. A flat sorted table with group headers is the simplest approach that conveys the grouping.

**Alternative considered**: Accordion/collapsible groups. Rejected — with only 14 blocks, collapsing adds clicks without benefit.

### 4. Optimistic UI update on save

**Decision**: Update the local signal state immediately on save, then revert if the API call fails.

**Rationale**: The PATCH endpoint is simple (single field update). Optimistic update makes the UI feel responsive. On failure, revert and show an error message.

## Risks / Trade-offs

- **[Stale data]** If another user changes a block's traversal time, this page won't reflect it until refresh. → Acceptable for an interview assignment; no polling needed.
- **[Validation]** The API may reject invalid traversal times (e.g., negative values). → Validate client-side: positive integer, minimum 1 second.

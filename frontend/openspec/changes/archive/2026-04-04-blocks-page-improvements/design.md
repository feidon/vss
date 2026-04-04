## Context

The `BlockConfigComponent` (`src/app/features/config/block-config.ts`) displays blocks in a grouped table with inline editing for traversal times. Three UX issues need fixing — all localized to this single component's template and one method.

Current state:
- Group column renders `{{ block.group }}` which shows "0" for ungrouped blocks
- Row height is not constrained, so switching between display span and input field causes layout shift
- `onBlur()` calls `cancelEdit()`, discarding edits when clicking outside

## Goals / Non-Goals

**Goals:**
- Show "-" in the group data cell for `group === 0`
- Prevent row height jitter when entering/exiting edit mode
- Save (not cancel) when the user clicks outside the edit input

**Non-Goals:**
- Changing group header labels (already "Ungrouped" via `group-label-display` spec)
- Changing keyboard behavior (Enter saves, Escape cancels — unchanged)
- Refactoring component structure or extracting sub-components

## Decisions

### 1. Conditional text in group column

Use Angular's ternary in the template: `{{ block.group === 0 ? '-' : block.group }}`.

**Alternative**: A pipe (e.g., `GroupDisplayPipe`). Rejected — a one-line ternary doesn't warrant a new file.

### 2. Fixed row height via min-height on `<td>`

Apply a Tailwind `h-9` (36px) class on the traversal time `<td>` to match the input field height. The input already has `py-1` padding; constraining the cell ensures the row doesn't shift.

**Alternative**: Render a hidden input at all times and toggle visibility. Rejected — adds DOM complexity for no gain. A simple fixed height achieves the same result.

### 3. Blur saves instead of cancels

Change `onBlur()` to call `save(block)` instead of `cancelEdit()`. This requires passing the block reference to `onBlur`. The `save()` method already handles validation (rejects invalid values), so no new validation path is needed.

**Alternative**: Use `(focusout)` event on a wrapper element. Rejected — `(blur)` on the input is simpler and already wired up.

**Race condition note**: When the user clicks another block's traversal time while one is already being edited, `blur` fires on the old input before `click` fires on the new one. Since `save()` is synchronous (optimistic update) and sets `editingBlockId` to `null`, the subsequent `startEdit()` from the click will work correctly.

## Risks / Trade-offs

- **Accidental saves**: Users who reflexively click away expecting cancel will now save. Mitigated by the fact that Escape explicitly cancels, and the original `block-list` spec defined blur-to-save as the intended behavior.
- **Validation on blur**: If the user types an invalid value and clicks away, `save()` will show the validation error but the input will already be gone (blur closed it). To handle this: if validation fails in `onBlur`, keep the edit open instead of closing.

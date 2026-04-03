## Why

The block configuration page has two UX issues:
1. The inline edit input has no click-outside-to-dismiss behavior — currently, blur auto-saves which can cause accidental saves when the user clicks away without intending to commit changes.
2. Blocks with `group: 0` display as "Group 0", but group 0 means the block has no interlocking group. This is confusing and should use a descriptive label instead.

## What Changes

- **Click-outside dismiss**: Clicking outside the edit input cancels the edit (reverts to original value) instead of auto-saving. Save only happens on explicit Enter key press.
- **Group 0 label**: Rename "Group 0" header to "Ungrouped" (or similar) to clarify that these blocks have no interlocking group.

## Non-goals

- No changes to the save/validation logic itself
- No changes to the API or data model (`group: 0` stays as-is in the backend)
- No changes to other pages or components

## Capabilities

### New Capabilities

- `click-outside-dismiss`: Click outside the inline edit input cancels editing without saving
- `group-label-display`: Display "Ungrouped" instead of "Group 0" for blocks with no interlocking group

### Modified Capabilities

_(none)_

## Impact

- **Component**: `BlockConfigComponent` (`src/app/features/block-config/block-config.ts`) — template and component logic changes
- **Tests**: `block-config.spec.ts` — update blur-save tests, add click-outside-cancel tests, update group header assertions

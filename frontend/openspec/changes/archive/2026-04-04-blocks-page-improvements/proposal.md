## Why

The block configuration page (`BlockConfigComponent`) has three UX issues: ungrouped blocks show "0" in the group column instead of a meaningful placeholder, row height shifts when entering edit mode (layout jitter), and clicking outside the edit input discards changes instead of saving them.

## What Changes

- Display "-" in the group column for blocks with `group: 0` (ungrouped), replacing the raw numeric "0"
- Apply fixed row height to block rows so the layout stays stable when the inline edit input appears
- Change blur behavior: clicking outside the traversal time input saves the value (like Enter) instead of cancelling (like Escape)

## Non-goals

- No changes to group header labels (already handled by `group-label-display` spec — "Ungrouped" header is correct)
- No changes to keyboard behavior (Enter to save, Escape to cancel remain unchanged)
- No backend API changes

## Capabilities

### New Capabilities
- `ungrouped-dash-display`: Show "-" in the group data cell for blocks with `group: 0`
- `stable-row-height`: Prevent row height change when inline edit input appears in traversal time column

### Modified Capabilities
- `click-outside-dismiss`: Change blur behavior from cancel to save — clicking outside the edit input now validates and saves the value

## Impact

- `src/app/features/config/block-config.ts` — All three changes are in this single component's template and `onBlur()` method

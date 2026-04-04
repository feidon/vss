## 1. Ungrouped dash display

- [x] 1.1 In `BlockConfigComponent` template, change group column from `{{ block.group }}` to `{{ block.group === 0 ? '-' : block.group }}`
- [x] 1.2 Add test: ungrouped block (group 0) renders "-" in group cell
- [x] 1.3 Add test: grouped block renders numeric group value in group cell

## 2. Stable row height

- [x] 2.1 Add `h-9` class to the traversal time `<td>` to fix row height across display/edit modes
- [x] 2.2 Verify visually that entering and exiting edit mode does not cause row height shift

## 3. Blur saves instead of cancels

- [x] 3.1 Change `onBlur()` to call `save(block)` instead of `cancelEdit()` — pass block reference via template `(blur)="onBlur(block)"`
- [x] 3.2 Handle validation failure on blur: if `save()` returns early due to invalid input, keep edit mode open (don't set `editingBlockId` to null)
- [x] 3.3 Add test: blurring input with valid value triggers save (PATCH call)
- [x] 3.4 Add test: blurring input with invalid value keeps edit mode open and shows validation error
- [x] 3.5 Add test: Escape still cancels without saving

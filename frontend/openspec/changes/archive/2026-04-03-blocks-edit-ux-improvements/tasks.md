## 1. Click-outside dismiss

- [x] 1.1 Change `onBlur()` in `BlockConfigComponent` to call `cancelEdit()` instead of `save()`
- [x] 1.2 Update existing blur-related tests in `block-config.spec.ts` to assert cancel (not save) on blur
- [x] 1.3 Add test: clicking outside input reverts to original value without API call

## 2. Group label display

- [x] 2.1 Update group header template to show "Ungrouped" when `g.group === 0`, "Group {n}" otherwise
- [x] 2.2 Update existing group header test assertions for group 0
- [x] 2.3 Add test: non-zero groups still display "Group {n}"

## 1. Block List Display

- [x] 1.1 Write test: component loads blocks from BlockService and renders a table with name, group, and traversal time columns
- [x] 1.2 Implement BlockConfigComponent: fetch blocks on init, store in signal, render grouped table with Tailwind styling
- [x] 1.3 Write test: blocks are grouped by interlocking group with group headers, sorted by name within each group
- [x] 1.4 Implement grouping logic: group blocks by `group` field, sort groups numerically, sort blocks by name within each group

## 2. Error Handling on Load

- [x] 2.1 Write test: display error message when GET /blocks fails
- [x] 2.2 Implement error state signal and error message UI for failed block loading

## 3. Inline Editing

- [x] 3.1 Write test: clicking traversal time value enters edit mode with a pre-filled input
- [x] 3.2 Write test: pressing Enter saves the value via PATCH and exits edit mode
- [x] 3.3 Write test: pressing Escape reverts to original value and exits edit mode without API call
- [x] 3.4 Write test: blurring the input saves the value via PATCH and exits edit mode
- [x] 3.5 Implement inline edit: track editing block ID in signal, toggle between display span and number input, handle keydown and blur events

## 4. Validation

- [x] 4.1 Write test: reject non-positive or non-integer values and show validation error
- [x] 4.2 Implement client-side validation: positive integer >= 1, prevent API call on invalid input

## 5. Save Feedback

- [x] 5.1 Write test: successful PATCH updates the displayed value
- [x] 5.2 Write test: failed PATCH reverts the value and shows an error message
- [x] 5.3 Implement optimistic update with rollback on failure, display error message on API error

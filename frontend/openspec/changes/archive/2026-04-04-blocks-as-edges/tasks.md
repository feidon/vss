## 1. Track Map: Blocks as Edge Labels

- [x] 1.1 In `track-map-editor.ts`, remove the block circle rendering (lines 98-111: `selectAll('circle.block')` section)
- [x] 1.2 Update the block label rendering (lines 113-125) to position text at (block.x, block.y) with styling suitable for edge labels (smaller font, gray fill, centered on edge)
- [x] 1.3 Verify connection lines still render correctly between all nodes (platform→block→block→platform chains)
- [x] 1.4 Update track-map-editor tests to assert no `circle.block` elements and presence of block name text labels

## 2. Error Handling: Robust Route Update Feedback

- [x] 2.1 In `schedule-editor.ts`, add `errorMessage = signal<string | null>(null)` alongside existing `conflicts` signal
- [x] 2.2 In `onRouteSubmitted`, clear both `conflicts` and `errorMessage` before the request
- [x] 2.3 In the error handler, add an `else` branch for non-409 errors that sets `errorMessage` to a generic string (e.g., "Failed to update route. Please try again.")
- [x] 2.4 Add an `@if (errorMessage())` block in the template to show a dismissible red alert banner with the error message
- [x] 2.5 Update schedule-editor tests to cover non-409 error scenarios (500, network error) and verify `errorMessage` is set

## 3. Verification

- [x] 3.1 Run `ng test` and confirm all existing and new tests pass
- [x] 3.2 Run `ng lint` and `npx prettier --check "src/**/*.{ts,html,css}"` to confirm no lint/format regressions

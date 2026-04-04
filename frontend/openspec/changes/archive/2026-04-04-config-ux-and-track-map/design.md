## Context

The block configuration page (`/blocks`) has several UX polish issues: the inline edit input is taller than the row causing layout shifts, the pencil icon disappears during editing, and click-outside behavior needs to trigger save. Separately, the track map page (`/map`) renders nodes via d3.js but the backend has no meaningful x,y geometry seeded — the map doesn't visually match the physical railway topology.

The block-config component (`features/config/block-config.ts`) uses Angular signals for state management with a `groupedBlocks` computed property that already sorts groups and blocks by name. The inline editor replaces the value span with an input field, but the input's padding makes it taller than the row. The pencil icon is embedded inside the value span and disappears when the input replaces it.

The track map editor (`features/schedule/track-map-editor.ts`) already renders nodes at their x,y coordinates using d3.js with linear scales. It just needs correct coordinates in the database.

## Goals / Non-Goals

**Goals:**
- Fix layout shift when toggling between display and edit modes in block config
- Make the pencil icon a persistent toggle that stays visible during editing
- Ensure click-outside-input saves the value
- Define and document node coordinates for the track map geometry

**Non-Goals:**
- Changing the block config table structure or columns
- Modifying the track map d3.js rendering logic (it already works with correct coordinates)
- Making the track map geometry user-editable in the frontend
- Adding new API endpoints

## Decisions

### 1. Fixed row height with compact input

**Decision:** Set a fixed `h-10` (40px) on each table row and use `py-0` + `h-8` (32px) on the input field so it fits within the row without causing shifts.

**Rationale:** The current `py-2` padding on rows plus the input's own padding/border creates a height mismatch. A fixed row height with a compact input eliminates the shift entirely.

**Alternative considered:** Using `box-border` and matching padding — rejected because it's fragile across browsers and harder to maintain.

### 2. Pencil icon outside the conditional block

**Decision:** Move the pencil icon SVG outside the `@if (editingBlockId() === block.id)` conditional so it renders in both display and edit modes. The icon sits to the right of both the value span and the input field, at a fixed position.

**Rationale:** The user wants the icon visible at all times and clickable as a toggle. Keeping it inside the conditional means it disappears during editing.

**Implementation:** The traversal time cell layout becomes:
```
<td class="h-10 px-3 py-0">
  <div class="flex items-center gap-2">
    @if (editing) {
      <input ... />
    } @else {
      <span>{{ value }}</span>
    }
    <button (click)="toggleEdit(block)">
      <svg pencil-icon />
    </button>
  </div>
</td>
```

The `toggleEdit` method checks if already editing this block → save, otherwise → start edit.

### 3. Click-outside via blur event (existing pattern)

**Decision:** Keep using the input's `(blur)` event for click-outside detection rather than adding a document-level click listener.

**Rationale:** The blur event already fires when the user clicks anywhere outside the input. The current code handles this correctly via `onBlur()`. The only issue was that clicking the pencil icon during editing caused a blur→save followed by a new startEdit, which we fix by making the icon a toggle with `(mousedown)` to prevent the blur race condition.

**Alternative considered:** Adding a `@HostListener('document:click')` — rejected because blur already provides the same behavior with less complexity and no need to track click targets.

### 4. Pencil icon click uses mousedown to prevent blur race

**Decision:** The pencil icon button uses `(mousedown.prevent)` instead of `(click)` to handle the toggle action.

**Rationale:** When the user clicks the pencil icon while editing, the input blur fires before the icon's click event. This causes a double-save (blur saves, then click tries to save again) or a reopen. Using `mousedown` with `preventDefault()` stops the blur from firing, giving the icon full control over save-and-close.

### 5. Track map geometry as DB seed data

**Decision:** Define coordinates in the spec as a reference table. The user will seed these into the database. No frontend code changes needed for the track map — it already renders nodes at their x,y coordinates.

**Rationale:** The Node model already has x,y fields. The d3.js renderer already positions nodes using these coordinates with linear scales. The only missing piece is meaningful coordinate data in the database.

## Risks / Trade-offs

- **[mousedown vs click]** Using `mousedown.prevent` on the pencil icon means the icon won't receive focus via click, which is fine since it's a toggle button, not an input. Screen readers still work via the button's role/aria attributes. → Mitigation: ensure the button has proper `aria-label`.

- **[Fixed row height]** Hard-coding `h-10` means if the font size or input design changes significantly, the row height may need manual adjustment. → Mitigation: use Tailwind's consistent sizing scale; `h-10` (40px) is standard for compact table rows with inputs.

- **[Geometry coordinates]** The coordinates are approximate and based on the reference image. If the track topology changes (new blocks/stations), coordinates need manual DB updates. → Mitigation: this is a fixed 14-block network; the topology is not expected to change.

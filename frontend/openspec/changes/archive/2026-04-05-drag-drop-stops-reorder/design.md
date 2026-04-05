## Context

The route editor's stops queue (`RouteEditorComponent`) stores stops as a `signal<readonly StopEntry[]>`. Users add stops by clicking platforms/yards on the track map, but the only way to fix ordering mistakes is to remove stops and re-add them. `@angular/cdk` v21.2.5 is already installed and includes `CdkDragDrop` — it just isn't wired up yet.

## Goals / Non-Goals

**Goals:**
- Enable drag-and-drop reordering of stops within the stops list
- Provide clear visual feedback during drag (placeholder, preview)
- Keep track map order numbers in sync after reorder
- Preserve immutable signal update pattern

**Non-Goals:**
- Reordering via the track map visualization
- Multi-select drag
- Undo/redo
- Custom keyboard reorder controls beyond CDK defaults

## Decisions

### 1. Use `@angular/cdk/drag-drop` (not a third-party library)

**Rationale:** Already in `package.json`, maintained by the Angular team, works natively with Angular signals and standalone components. No new dependency needed.

**Alternatives considered:**
- **SortableJS / ngx-sortable**: Adds an external dependency for functionality CDK already provides.
- **Native HTML drag-and-drop API**: Lower-level, no built-in animation, poor touch support, requires more boilerplate.

### 2. Reorder via immutable signal update

On `cdkDropListDropped`, compute the new array using `moveItemInArray`-style logic on a shallow copy, then call `this.stops.set(reordered)`. This preserves the project's immutable update convention.

**Rationale:** Signals are the single source of truth. The track map's order numbers are derived from `queuedStopIds` (a computed signal), so they update automatically when the stops signal changes.

### 3. Minimal visual treatment — drag handle + drop placeholder

- Add a drag handle (grip icon) on the left side of each stop row.
- CDK provides a `.cdk-drag-placeholder` class for the drop target gap and `.cdk-drag-preview` for the floating element. Style these with Tailwind utilities via a small component CSS block (CDK injects the preview outside the component DOM, so global/component styles are needed).

**Rationale:** Keeps the change small and consistent with the existing row design. The grip icon signals draggability without cluttering the UI.

## Risks / Trade-offs

- **CDK preview styling**: The drag preview is rendered outside the component's view encapsulation. → Mitigation: Use `:host` or a dedicated CSS class with `ViewEncapsulation.None` scoped to just the preview, or use `cdkDragPreviewClass`.
- **Touch devices**: CDK drag-drop supports touch, but the small row height may make targets hard to grab. → Mitigation: The drag handle provides a clear touch target; row height (py-2) is adequate for mobile.
- **List length**: Routes are typically 2–8 stops, so performance is not a concern. No virtualization needed.

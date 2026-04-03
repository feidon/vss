## Context

The `BlockConfigComponent` (`src/app/features/block-config/block-config.ts`) provides inline editing of block traversal times. Currently:
- Clicking a traversal time value switches to an `<input>` field
- The `(blur)` event auto-saves the value via `onBlur()` → `save()`
- Group headers display "Group {n}" for all groups, including group 0 which semantically means "no interlocking group"

## Goals / Non-Goals

**Goals:**
- Click outside the edit input cancels editing (dismiss without saving)
- Display "Ungrouped" instead of "Group 0" for blocks with `group: 0`

**Non-Goals:**
- No shared click-outside directive — this is a single-use behavior in one component
- No changes to the block API or data model
- No changes to Enter-to-save or Escape-to-cancel behavior

## Decisions

### 1. Blur cancels instead of saves

**Decision**: Change `(blur)` handler from `save()` to `cancelEdit()`.

**Rationale**: The current blur-to-save behavior causes accidental saves when users click away. Standard UX for inline editing: Enter = commit, Escape/click-away = cancel. No click-outside directive needed — the native `blur` event already fires when clicking outside.

**Alternative considered**: A `@HostListener('document:click')` or custom click-outside directive. Rejected — blur already covers this case and is simpler.

### 2. Conditional group label in template

**Decision**: Use a ternary expression in the template: `g.group === 0 ? 'Ungrouped' : 'Group ' + g.group`.

**Rationale**: Simple, localized change. No need for a pipe or helper — this is a one-off display concern in a single template location.

**Alternative considered**: A `groupLabel` pipe. Rejected — over-engineering for a single usage site.

## Risks / Trade-offs

- **Behavior change for existing users**: Users accustomed to blur-to-save will now need to press Enter. Low risk given the small user base (interview project). → Mitigation: none needed.
- **Unsaved edits lost on accidental click-away**: User may type a value then accidentally click outside, losing changes. → Acceptable: this is standard inline-edit behavior (matches spreadsheet/table editors).

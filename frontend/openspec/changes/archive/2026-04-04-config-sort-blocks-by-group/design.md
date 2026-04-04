## Context

The `BlockConfigComponent` displays blocks grouped by interlocking group. The `groupedBlocks` computed signal sorts blocks within each group using `a.name.localeCompare(b.name)`, which is lexicographic. This causes "B10" to sort before "B2" and "B13" before "B3" — confusing for users scanning the table.

## Goals / Non-Goals

**Goals:**
- Blocks within each group display in natural numeric order (B1, B2, B3, ..., B10, B13, B14)

**Non-Goals:**
- Changing group ordering (already correct: ascending by group number)
- Server-side sorting or API changes
- User-configurable sort columns

## Decisions

### Use `localeCompare` with `{ numeric: true }` option

**Rationale:** The `Intl.Collator` numeric option (exposed via `localeCompare`) handles natural sorting natively — no custom parsing needed. It correctly sorts "B2" before "B10" by treating embedded digit sequences as numbers.

**Alternative considered:** Custom regex-based natural sort (extract numeric suffix, compare). Rejected — `localeCompare({ numeric: true })` is a one-line change with identical behavior and no maintenance cost.

**Change location:** `BlockConfigComponent.groupedBlocks` computed signal in `src/app/features/config/block-config.ts`, line 123.

```typescript
// Before
blocks: [...blocks].sort((a, b) => a.name.localeCompare(b.name)),

// After
blocks: [...blocks].sort((a, b) => a.name.localeCompare(b.name, undefined, { numeric: true })),
```

## Risks / Trade-offs

- **[Risk] Browser compatibility** → `localeCompare` with `numeric` option is supported in all modern browsers and Node.js 14+. No risk for this project.
- **[Risk] Locale-dependent sorting** → Using `undefined` locale defers to the runtime default. Block names are ASCII alphanumeric (B1-B14), so locale has no effect on ordering. No mitigation needed.

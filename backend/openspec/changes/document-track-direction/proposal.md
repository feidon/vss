## Why

The track network is directional — `NodeConnection(from_id, to_id)` defines directed edges, B1/B2 are bidirectional, and all other blocks are strictly unidirectional. However, neither `CLAUDE.md` nor `openspec/config.yaml` document the full adjacency list or direction semantics. This makes it hard for contributors (and AI agents) to reason about route validity without reading seed code.

## What Changes

- **CLAUDE.md**: Add the complete track adjacency list with direction notation (`->` / `<-`) to the Track Network section.
- **openspec/config.yaml**: Add the same adjacency list and direction semantics to the `context` block so all future changes have this context.

No code changes — the domain model (`NodeConnection`), seed data, and `RouteFinder` already enforce directionality correctly.

## Capabilities

### New Capabilities

(none — documentation-only change)

### Modified Capabilities

(none — no spec-level behavior changes)

## Impact

- `CLAUDE.md` — updated Track Network section
- `openspec/config.yaml` — updated context block

## Non-goals

- Adding a `direction` field to `NodeConnection` — the existing `from_id`/`to_id` already encodes direction.
- Changing seed data or database schema.
- Modifying the `RouteFinder` or conflict detection logic.

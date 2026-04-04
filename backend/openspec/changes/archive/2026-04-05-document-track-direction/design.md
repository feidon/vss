## Context

The track network uses directed edges (`NodeConnection(from_id, to_id)`) with B1/B2 bidirectional and all others unidirectional. This is implemented correctly in `infra/seed.py` and used by `RouteFinder` (BFS on directed adjacency). However, the adjacency list and direction semantics are not documented in `CLAUDE.md` or `openspec/config.yaml`, forcing readers to trace seed code to understand valid routes.

## Goals / Non-Goals

**Goals:**
- Add the full adjacency list with `->` / `<-` direction notation to `CLAUDE.md` and `openspec/config.yaml`
- Make direction semantics explicit (B1/B2 bidirectional, rest unidirectional)

**Non-Goals:**
- Code changes — the domain model already handles direction correctly
- Schema or migration changes
- Changing the `NodeConnection` value object

## Decisions

1. **Use the same notation as `infra/seed.py` docstring** — the `Y <- B1 -> P1A` format is already established in the codebase and matches the assignment specification. No reason to invent a different representation.

2. **Place adjacency list in Track Network section of both files** — this is the natural location since both files already have a Track Network subsection.

## Risks / Trade-offs

- [Duplication between CLAUDE.md and config.yaml] → Acceptable since both serve different audiences (developers vs. OpenSpec agents) and the data is static reference data that won't change.

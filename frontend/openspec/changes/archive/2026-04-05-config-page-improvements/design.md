## Context

The config page (`/config`) currently renders only `BlockConfigComponent`. The block table's group column displays a "-" for ungrouped blocks, but without centering — the grouped rows use an `inline-flex items-center` badge while the ungrouped rows use a plain `<span>` with no flex/centering. There is no vehicle listing anywhere on the config page despite `VehicleService` and `GET /api/vehicles` already being available.

## Goals / Non-Goals

**Goals:**
- Center-align the "-" placeholder in the group column to match the visual weight of group badges.
- Add a read-only vehicle list section below the block config table, showing all vehicles sorted by ID.

**Non-Goals:**
- No vehicle CRUD operations.
- No changes to block editing or track map overview.
- No new API endpoints or backend changes.

## Decisions

### 1. Fix group column centering via `text-center` on the cell

**Rationale:** The group badge already uses `inline-flex items-center` for self-alignment. The simplest fix is adding `text-center` to the `<td>` cell so both the badge and the "-" span are horizontally centered within the column. This avoids wrapping the "-" in unnecessary flex containers.

**Alternative considered:** Wrapping the "-" in an identical `inline-flex` badge structure — rejected as over-engineering for a simple text placeholder.

### 2. New standalone `VehicleListComponent` in `features/config/`

**Rationale:** Follows the existing pattern — `ConfigComponent` is a thin wrapper that imports feature sub-components. A standalone `VehicleListComponent` keeps the vehicle list self-contained and testable independently. Placing it in `features/config/` co-locates it with the config page.

**Alternative considered:** Adding vehicle listing directly into `BlockConfigComponent` — rejected because it violates single-responsibility and the existing separation pattern.

### 3. Sort vehicles by name (natural alphanumeric sort)

**Rationale:** Vehicle IDs are UUIDs, which have no meaningful sort order. Sorting by `name` (e.g., V1, V2, V3) gives a predictable, user-friendly display order. The backend `GET /api/vehicles` response order is not guaranteed, so sorting must happen client-side.

### 4. Reuse existing table styling from BlockConfigComponent

**Rationale:** Consistent visual design across the config page. The block table already has a well-established dark-theme table style with Tailwind utilities. The vehicle list should use the same patterns (same header colors, row styling, padding, font choices).

## Risks / Trade-offs

- **[Minimal risk] Vehicle list grows large** — Currently only 3 vehicles (V1, V2, V3). No pagination needed, but if the fleet grows significantly this would need revisiting. → Mitigation: acceptable for current scale, defer pagination.
- **[Low risk] API call on every config page visit** — VehicleService makes a fresh HTTP call each load. → Mitigation: acceptable since the vehicle list is small and rarely changes; no caching needed now.

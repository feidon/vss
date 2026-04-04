## Context

The schedule editor's track map (`track-map-editor.ts`) renders the full graph — platforms, yards, and blocks — as D3 SVG nodes. Blocks are drawn as small gray circles with labels. However, blocks are just track segments between platforms/yards and should be visualized as edge labels, not discrete nodes.

Separately, the route update error handler (`schedule-editor.ts:85-92`) only handles HTTP 409. Any other error (network failure, 422 validation, 500 server error) is silently swallowed — the user gets no feedback.

The graph data model: `GraphResponse` contains `nodes` (block, platform, yard — all with x/y coordinates) and `connections` (from_id/to_id pairs). Connections chain through blocks: platform → block → block → platform. Each block node sits geometrically on the edge between its neighbors.

## Goals / Non-Goals

**Goals:**
- Render blocks as text labels on edges, not as circle nodes
- Handle all HTTP error statuses from route updates with user-visible feedback
- Keep existing conflict alert component and its rendering of all 4 conflict types

**Non-Goals:**
- Changing the backend API or graph data model
- Adding the unused `POST /api/routes/validate` endpoint call
- Redesigning the conflict-alert component layout
- Changing the config page track map (separate component)

## Decisions

### 1. Block label placement: midpoint of the connection edge that passes through the block

Each block has x/y coordinates in the graph data. Since connections chain through blocks (platform→block→…→block→platform), each block node lies on one or more connection edges. Rather than computing complex edge midpoints, use the block's existing x/y coordinates directly as the label anchor point — the backend already positions blocks on their edges geometrically. Simply remove the circle rendering and keep the text label at (block.x, block.y).

**Alternative considered:** Calculate midpoint between `from_id` and `to_id` for each connection, then match blocks to connections. Rejected — unnecessarily complex when block coordinates already represent the correct position.

### 2. Error handling: add an `errorMessage` signal alongside existing `conflicts` signal

The schedule editor already has `conflicts = signal<ConflictResponse | null>(null)`. Add a separate `errorMessage = signal<string | null>(null)` for non-409 errors. The template shows either the conflict alert OR the error message, never both (since `conflicts` is cleared on each submission).

**Alternative considered:** Reuse the `conflicts` signal with a union type. Rejected — conflates two different concerns and complicates the conflict-alert component interface.

### 3. Error message display: simple inline alert in the template

For non-409 errors, show a red alert banner similar to the conflict alert but with just a text message (e.g., "Failed to update route. Please try again."). No need for a separate component — a simple `@if` block in the template suffices.

## Risks / Trade-offs

- **Block labels may overlap on dense edges** → Acceptable for now; the track map has only 14 blocks spread across 6 platforms and 1 yard. Revisit if the network grows.
- **Non-409 error messages are generic** → Trade-off for simplicity. Backend error messages may not be user-friendly, so a generic message is safer than exposing raw server errors.

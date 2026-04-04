# Backend Requirements: Blocks as Edges

## Summary

Change the graph API so blocks are returned as **edges** instead of nodes. Junction positions (where blocks meet) are returned in a separate `junctions` array — they are read-model data seeded in the DB, not domain entities.

## New Graph Response Schema

```json
{
  "nodes": [
    { "type": "platform", "id": "uuid", "name": "P1A", "x": 0.0, "y": 0.0 },
    { "type": "yard", "id": "uuid", "name": "Y", "x": 5.0, "y": 0.0 }
  ],
  "junctions": [
    { "id": "uuid", "x": 2.0, "y": 0.0 }
  ],
  "edges": [
    {
      "id": "uuid",
      "name": "B1",
      "group": 1,
      "traversal_time_seconds": 30,
      "from_id": "uuid",
      "to_id": "uuid"
    }
  ],
  "stations": [ "... unchanged ..." ],
  "vehicles": [ "... unchanged ..." ]
}
```

### Node types (domain entities)

| Type | Fields | Description |
|------|--------|-------------|
| `platform` | `id, name, x, y` | Train platform (clickable stop) |
| `yard` | `id, name, x, y` | Yard (clickable stop) |

**Blocks are removed from nodes entirely.**

### Junctions (read-model, seeded in DB)

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string (uuid)` | Junction ID |
| `x` | `number` | X coordinate for rendering |
| `y` | `number` | Y coordinate for rendering |

Junction positions are where blocks meet (not platforms/yards). They are **not domain entities** — just rendering coordinates stored in the read model.

### Edge (= Block)

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string (uuid)` | Block ID |
| `name` | `string` | Block display name (e.g. "B1") |
| `group` | `number` | Interlocking group |
| `traversal_time_seconds` | `number` | Time to traverse |
| `from_id` | `string (uuid)` | Source — a platform, yard, or junction ID |
| `to_id` | `string (uuid)` | Target — a platform, yard, or junction ID |

### What changes

- `connections` field is **replaced** by `edges`
- `junctions` is a **new** field
- Block nodes are **removed** from `nodes`

### Service detail route

`ServiceDetailResponse.route` should contain only platform/yard nodes (the stops). No blocks, no junctions.

## Unchanged APIs

- `PATCH /api/services/{id}/route` — still sends `stops[]` with platform/yard node IDs
- `POST /api/routes/validate` — same
- `GET /api/services` — same

## How the frontend uses this

- Builds a position map by merging `nodes` + `junctions` by ID
- Edges reference IDs from either collection — the renderer draws lines between the looked-up positions
- Junctions render as small non-interactive dots
- Platforms/yards render as clickable circles
- Block labels appear at the midpoint of their edge line

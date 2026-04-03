# Backend Changes Needed for Frontend Redesign

## Context

Analysis of the frontend TODO list against current backend API capabilities.
The backend stores services with: `id`, `name`, `vehicle_id`, `route` (JSONB, expanded full path), `timetable` (JSONB).

**Key insight:** The original stops, dwell times, and start time can all be **derived** from existing persisted data:
- **stops** = nodes in `route` where `type != "block"` (i.e. platform/yard nodes)
- **dwell_time** per stop = `departure - arrival` from the matching timetable entry
- **start_time** = `timetable[0].arrival`

No new database columns are needed.

---

## Backend Change: Enrich service list response

**Why:** The list endpoint (`GET /api/services`) currently returns only `{id, name, vehicle_id, vehicle_name}`. The viewer page needs start time, origin, and destination — but the list response has no route or timetable data, so the frontend can't derive these without fetching every service's detail individually.

**Change — add to each service in the list response:**
- `start_time`: integer (epoch seconds) — derived from `timetable[0].arrival`
- `origin_name`: string (e.g. "P1A", "Y") — first node name in route
- `destination_name`: string (e.g. "P2B") — last node name in route

---

## Frontend Can Derive (no backend change)

Everything else the frontend needs is already available from the **detail** response (`GET /api/services/{id}`), which returns both `route` (with node types) and `timetable` (with arrival/departure):

| Need | How to derive |
|------|---------------|
| Original stops (queue) | Filter `route` where `type !== "block"` |
| Dwell time per stop | Timetable entry: `departure - arrival` for that node |
| Start time | `timetable[0].arrival` |
| Expandable path summary | Filter route for stop nodes, join names from graph |
| Conflict display | 409 response already implemented |

---

## No Backend Changes Needed

All other frontend TODO items are purely UI/UX:

| Item | Why no backend change |
|------|----------------------|
| Reorganize to two tabs (viewer, settings) | Routing/layout only |
| Create service button in viewer | Already have `POST /api/services` |
| Create dialog with name/vehicle/start time | start_time deferred to route save |
| Jump to editor sub-page after create | Frontend routing |
| Editor is a track map | Graph data already available via `GET /api/graph` |
| Edit and delete buttons in viewer | `DELETE /api/services/{id}` exists; edit is navigation |
| Back-to-list button visibility | CSS/UX |
| Choose yard in platform selection | Graph data already includes yard info via stations |
| Show conflict messages | 409 conflict response already implemented |
| Track map in editor | d3.js rendering; graph data available |
| Blocks: show "-" for ungrouped | Frontend display logic |
| Blocks: fixed row height during edit | CSS |
| Blocks: click-outside to save | Frontend event handling |

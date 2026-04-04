## Context

The config page (`/config`) has two broken interactions:

1. **Click-outside dismiss broken**: `BlockConfigComponent` renders an `<input>` when editing a traversal time, with `(blur)="onBlur(block)"` as the dismiss mechanism. However, `startEdit()` never programmatically focuses the input. If the user opens editing via the pencil icon (mousedown), the input appears but is not focused — so clicking elsewhere never triggers blur and the edit stays open.

2. **Track map data source missing**: `TrackMapOverviewComponent` calls `GraphService.getGraph()` which hits `GET /api/graph`. This endpoint does not exist in the backend — no graph router is registered in `main.py`. The schedule editor's track map works because it gets graph data embedded in `GET /api/services/{id}` response.

## Goals / Non-Goals

**Goals:**
- Auto-focus the input field when inline editing starts, so blur-based click-outside dismiss works
- Make the config page track map load graph data from an existing backend endpoint

**Non-Goals:**
- Changing the d3.js rendering logic in `TrackMapEditorComponent`
- Modifying backend routes (frontend-only fix preferred)
- Changing the schedule editor's track map behavior

## Decisions

### 1. Auto-focus via `afterNextRender`

**Decision**: Use Angular's `afterNextRender()` to focus the input after it's rendered.

**Rationale**: The input is conditionally rendered inside `@if (editingBlockId() === block.id)`. When `startEdit()` sets the signal, Angular needs a render cycle to create the DOM element. Using `afterNextRender()` (from `@angular/core`) schedules the focus call after the next render completes.

**Alternative considered**: Using `autofocus` attribute — doesn't work reliably with Angular's conditional rendering since the element is recreated each time. ViewChild query would also work but requires a template ref and is more boilerplate.

### 2. Frontend workaround for graph data: add backend `GET /api/graph` route

**Decision**: Add a `GET /api/graph` route to the backend. The backend already has `GraphAppService` and `get_graph_service` dependency wired up in `api/dependencies.py` — it just lacks a route file.

**Rationale**: The frontend's `GraphService.getGraph()` calling `GET /api/graph` is the correct design. The graph is a standalone resource (network topology) that shouldn't require loading a service first. Adding the missing backend route is a 1-file addition.

**Alternative considered**: Having the frontend fetch graph data from an arbitrary service detail (`GET /api/services/{id}`) — this is a hack because (a) there may be no services yet, (b) it loads unnecessary service data, and (c) the graph is conceptually independent of any service.

## Risks / Trade-offs

- **[Risk] `afterNextRender` timing**: The input may not be the only element rendered in that cycle. → **Mitigation**: Query specifically by CSS selector or template ref to ensure we focus the correct element.
- **[Risk] Backend route addition is cross-repo**: This change spans frontend + backend. → **Mitigation**: The backend change is minimal (one route file + register in main.py). The `GraphAppService` and its dependency injection are already wired.

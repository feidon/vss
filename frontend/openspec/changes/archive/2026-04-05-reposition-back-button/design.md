## Context

The schedule editor (`schedule-editor.ts`) displays a "← Back to Schedule" button inline with the service name in a `flex items-center gap-4` row. This makes both elements compete for visual attention and clutters the header.

Current HTML structure:
```html
<div class="mb-4 flex items-center gap-4">
  <a routerLink="/schedule" class="rounded bg-gray-200 px-4 py-2 text-sm font-medium hover:bg-gray-300">
    ← Back to Schedule
  </a>
  <h2 class="text-xl font-semibold">{{ service()!.name }}</h2>
</div>
```

## Goals / Non-Goals

**Goals:**
- Move the back link above the service name as a small text link (not a button)
- Give the service name clear visual dominance as the page heading

**Non-Goals:**
- Changing navigation behavior or target route
- Adding breadcrumb navigation
- Modifying other components

## Decisions

**1. Stack vertically instead of inline row**

Change from a single flex row to two stacked elements: a small text link on top, heading below. This is a common pattern (e.g., GitHub's "← Back to repo" above page titles).

Alternative considered: placing the button in a top navbar — rejected as overkill for a single link.

**2. Text link instead of styled button**

Replace `rounded bg-gray-200 px-4 py-2` button styling with a minimal `text-sm text-gray-500 hover:text-gray-700` text link. The back navigation is secondary to the page content.

Alternative considered: keeping button style but making it smaller — still too prominent.

## Risks / Trade-offs

- [Reduced discoverability] The link becomes less visually prominent → Acceptable since the browser back button and the sidebar also provide navigation.

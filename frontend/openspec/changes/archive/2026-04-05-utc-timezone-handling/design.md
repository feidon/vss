## Context

Time values flow through the VSS frontend in three places:

1. **Input**: User picks a start time via `<input type="datetime-local">` in `RouteEditorComponent`. The value is a local-time string (e.g., `"2024-01-15T08:00"`) converted to epoch via `new Date(str).getTime() / 1000`.
2. **API ↔ Frontend**: All API payloads use UTC epoch seconds (`TimetableEntry.arrival`, `departure`, `UpdateRouteRequest.start_time`, conflict `overlap_start/end`).
3. **Display**: Epoch seconds are rendered via `EpochTimePipe` (uses `getHours()`), `RouteEditorComponent.formatTime()` (uses `toLocaleTimeString()`), and `ConflictAlertComponent.formatTime()` (same). These all use implicit local timezone.

The conversions work by accident — JavaScript's `Date` constructor interprets timezone-less strings as local time, and `getHours()` returns local hours. But there's no explicit contract, no shared utility, and duplicated formatting logic in two components.

## Goals / Non-Goals

**Goals:**

- Single `TimeUtils` utility in `shared/utils/` for all epoch ↔ local conversions
- Every time conversion goes through `TimeUtils` — no inline `new Date()` for time formatting
- `EpochTimePipe` delegates to `TimeUtils` for display formatting
- Inline `formatTime()` methods in `RouteEditorComponent` and `ConflictAlertComponent` replaced by `EpochTimePipe`
- `datetime-local` ↔ epoch conversion in `RouteEditorComponent` uses `TimeUtils`

**Non-Goals:**

- Adding a date/time library — native `Date` and `Intl.DateTimeFormat` are sufficient
- Timezone selector or user-configurable timezone
- Changing API contracts — epoch seconds remain the wire format
- Modifying `dwell_time` handling (it's a duration, not a timestamp)

## Decisions

### 1. Pure functions in `shared/utils/time-utils.ts` (not an injectable service)

These are stateless transformations with no dependencies. A utility file with exported pure functions is simpler than an `@Injectable` service and avoids unnecessary DI ceremony.

**Alternative considered**: Angular service with `inject()` — rejected because there's no state, no configuration, and no dependencies to inject. Pure functions are easier to test and tree-shake.

### 2. Three core functions

```
localDatetimeToEpoch(localStr: string): number
  — Converts datetime-local input string → UTC epoch seconds

epochToLocalDatetime(epoch: number): string
  — Converts UTC epoch seconds → datetime-local format string (for input pre-fill)

epochToDisplayTime(epoch: number): string
  — Converts UTC epoch seconds → HH:MM:SS local-time display string
```

All three use the browser's local timezone implicitly (via `Date` constructor and `getHours()` etc.). The key change is centralizing these conversions, not changing the underlying timezone mechanism.

**Alternative considered**: Using `Intl.DateTimeFormat` for display — possible future enhancement but unnecessary for now since the existing `HH:MM:SS` format is consistent and sufficient.

### 3. `EpochTimePipe` delegates to `epochToDisplayTime()`

The pipe's `transform()` method calls `epochToDisplayTime()` for the actual formatting. The pipe remains the Angular-template-friendly wrapper; the logic lives in the testable pure function.

### 4. Replace inline `formatTime()` in components with `EpochTimePipe`

Both `RouteEditorComponent` and `ConflictAlertComponent` have identical `formatTime()` methods. Replace these with the `epochTime` pipe in templates. This eliminates duplication and ensures consistent formatting across all time displays.

**Note**: The current `toLocaleTimeString()` format will change to `HH:MM:SS` (padded, 24h). This is a minor visual change but provides consistency.

## Risks / Trade-offs

- **[Minor visual change]** `toLocaleTimeString()` is locale-dependent (e.g., "10:13:20 PM" in en-US) while `epochToDisplayTime()` returns 24h format "22:13:20". → Acceptable for a railway scheduling tool where 24h time is standard.
- **[Test timezone sensitivity]** Tests using fixed epoch values produce different local times in different timezones. → `TimeUtils` tests should use `epochToDisplayTime` with known offsets or test the round-trip `localDatetimeToEpoch` → `epochToLocalDatetime` which is timezone-independent.

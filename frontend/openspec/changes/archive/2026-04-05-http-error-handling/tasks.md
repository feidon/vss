## 1. Shared Utilities

- [x] 1.1 Create `extractErrorMessage` function in `src/app/shared/utils/error-utils.ts` — handles 500+ (constant message), 422/4xx `detail` string, `detail.message` object, and fallback
- [x] 1.2 Create `ErrorAlertComponent` in `src/app/shared/components/error-alert.ts` — `message` input, `dismiss` output, `×` close button top-right, red-bordered alert box matching `ConflictAlertComponent` style

## 2. Schedule Editor

- [x] 2.1 Replace inline error message markup in `ScheduleEditorComponent` with `ErrorAlertComponent`
- [x] 2.2 Use `extractErrorMessage` in the route update error handler (non-409 branch) to parse 422 and 500 responses

## 3. Schedule List

- [x] 3.1 Add `errorMessage` signal to `ScheduleListComponent`
- [x] 3.2 Add error handlers to `loadServices()`, `deleteService()`, and `getService()` (detail fetch) using `extractErrorMessage`
- [x] 3.3 Add `ErrorAlertComponent` to the schedule list template

## 4. Block Config

- [x] 4.1 Replace plain `<p class="text-red-600">` error display in `BlockConfigComponent` with `ErrorAlertComponent`

## 5. Create Service Dialog

- [x] 5.1 Add error message display for `createService()` failures using `extractErrorMessage` — show in dialog, reset saving state
- [x] 5.2 Replace plain load error `<p>` with `ErrorAlertComponent` or consistent styled error (dialog context may warrant inline text — match dialog visual pattern)

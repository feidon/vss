## 1. Model Update

- [x] 1.1 Remove `message` field from `ErrorDetail` interface in `src/app/shared/models/error.ts`

## 2. Error Utility Update

- [x] 2.1 Remove `detail.message` fallback branch (line 92) inside the `error_code` block in `extractErrorMessage`
- [x] 2.2 Remove standalone `detail.message` object check (lines 95-96) in `extractErrorMessage`

## 3. Test Updates

- [x] 3.1 Remove `message` field from all mock error payloads in `error-utils.spec.ts`
- [x] 3.2 Update "fall back to backend message when UUID not in name map" test — expect `fallback` instead of the old `message` value
- [x] 3.3 Update "fall back to backend message for unknown error code" test — expect `fallback` instead of the old `message` value
- [x] 3.4 Remove "return detail.message when detail is an object without error_code" test (dead path)
- [x] 3.5 Run `ng test` and verify all tests pass

## 4. Spec Updates

- [x] 4.1 Update `openspec/specs/structured-error-display/spec.md` — remove `message` from `ErrorDetail`, update fallback scenarios
- [x] 4.2 Update `openspec/specs/error-alert/spec.md` — replace "object detail containing message" scenario with "structured error_code detail" scenario

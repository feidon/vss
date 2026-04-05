## 1. Frontend Error Formatter

- [x] 1.1 Add `INTERVAL_BELOW_MINIMUM` entry to `ERROR_FORMATTERS` in `src/app/shared/utils/error-utils.ts` — read `requested_interval` and `minimum_interval` from context, return formatted string or `null` if fields missing

## 2. Tests

- [x] 2.1 Add test case in `error-utils.spec.ts`: valid context → formatted message `"Interval 59s is below the minimum of 60s due to interlocking constraints."`
- [x] 2.2 Add test case in `error-utils.spec.ts`: missing context fields → returns fallback message

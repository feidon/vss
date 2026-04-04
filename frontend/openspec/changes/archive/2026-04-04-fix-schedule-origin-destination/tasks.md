## 1. Investigate Root Cause

- [x] 1.1 Compare actual API response field names with `ServiceResponse` interface — check if `origin`/`destination` fields match the JSON keys returned by `GET /api/services`
- [x] 1.2 Verify the template binding in `ScheduleListComponent` correctly accesses the origin/destination values from the response

## 2. Fix Implementation

- [x] 2.1 Fix the `ServiceResponse` interface or template binding so origin and destination columns render the correct string names from the API
- [x] 2.2 Ensure null values still display "—" (em dash) as fallback

## 3. Testing

- [x] 3.1 Update or add unit test assertions in `schedule-list.spec.ts` to explicitly verify origin and destination column text content
- [x] 3.2 Run `ng test` and `ng lint` to confirm all tests pass

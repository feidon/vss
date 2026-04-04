## 1. RouteFinder Edge Cases

- [x] 1.1 Add tests for bidirectional block paths (Y→P1A via B1, Y→P1B via B2, P1A→Y reverse) in `tests/domain/test_route_finder.py`
- [x] 1.2 Add test for duplicate consecutive stops raising DomainError (P1A→P1A)
- [x] 1.3 Add test for `build_full_path` starting from Yard (Y→P1A = [Y, B1, P1A])
- [x] 1.4 Add test for `build_full_path` ending at Yard (P1A→Y = [P1A, B1, Y])
- [x] 1.5 Add test for full round trip path (Y→P1A→P2A→P3A→P2B→P1A→Y)

## 2. RouteBuilder Edge Cases

- [x] 2.1 Add test for yard as first stop (Y→P1A) with correct node types and timing in `tests/domain/test_route_builder.py`
- [x] 2.2 Add test for yard as last stop (P1A→Y)
- [x] 2.3 Add test for three-stop timetable timing continuity (departure[i] == arrival[i+1])
- [x] 2.4 Add test for yard dwell time computation (departure = arrival + dwell)
- [x] 2.5 Add test for four-stop route (P1A→P2A→P3A→P2B = 10 nodes)

## 3. Conflict Shared Utilities

- [x] 3.1 Create new file `tests/domain/test_conflict_shared.py`
- [x] 3.2 Add `find_time_overlaps` tests: empty input, single entry, overlapping pair, touching boundaries, unsorted input, multiple overlapping pairs
- [x] 3.3 Add `build_vehicle_schedule` tests: no matching vehicle, sorted by start time
- [x] 3.4 Add `build_occupancies` tests: empty services, mixed block/platform entries, grouping by interlocking group

## 4. Conflict Detection Edge Cases

- [x] 4.1 Add vehicle conflict tests: single service, multiple discontinuities, combined overlap+discontinuity in `tests/domain/test_conflict.py`
- [x] 4.2 Add interlocking tests: same-block same-group skipped, different groups no conflict, multi-group conflicts
- [x] 4.3 Add block conflict tests: multiple blocks with overlaps, touching boundary not reported
- [x] 4.4 Add battery tests: empty steps, single block traversal, exactly-at-critical boundary
- [x] 4.5 Add `ServiceConflicts.has_conflicts` tests: only block conflicts, only interlocking conflicts, all empty

## 5. Service Model Edge Cases

- [x] 5.1 Add equality tests: two None-id services not equal, None-id self-equality, None vs non-None id in `tests/domain/test_service.py`
- [x] 5.2 Add hash tests: two None-id services distinct in set
- [x] 5.3 Add `update_route` tests: empty route rejected, single-node route accepted
- [x] 5.4 Add equality test: Service compared to non-Service returns False

## 6. Final Verification

- [x] 6.1 Run full domain test suite (`uv run pytest tests/domain/ -v`) and verify all tests pass
- [x] 6.2 Run Ruff check and format on all modified test files

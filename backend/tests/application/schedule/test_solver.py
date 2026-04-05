from application.schedule.model import SolverInput
from application.schedule.route_variant import compute_route_variants
from application.schedule.solver import solve_schedule
from infra.seed import (
    VEHICLE_ID_BY_NAME,
    create_blocks,
    create_connections,
    create_stations,
)


def _build_solver_input(
    interval: int = 360,
    num_vehicles: int = 2,
    dwell: int = 30,
    start: int = 0,
    end: int = 5400,
) -> SolverInput:
    blocks = create_blocks()
    variants = compute_route_variants(
        stations=create_stations(),
        blocks=blocks,
        connections=create_connections(),
        dwell_time_seconds=dwell,
    )
    vehicle_ids = list(VEHICLE_ID_BY_NAME.values())[:num_vehicles]

    interlocking_groups: dict[int, list] = {}
    for b in blocks:
        if b.group != 0:
            interlocking_groups.setdefault(b.group, []).append(b.id)

    return SolverInput(
        variants=variants,
        num_vehicles=num_vehicles,
        vehicle_ids=vehicle_ids,
        trips_per_vehicle=max((end - start) // (num_vehicles * interval), 1),
        interval_seconds=interval,
        start_time=start,
        end_time=end,
        min_yard_dwells=[v.num_blocks * 12 for v in variants],
        cycle_times=[v.cycle_time for v in variants],
        interlocking_groups=interlocking_groups,
    )


class TestSolveSchedule:
    def test_feasible_returns_assignments(self):
        inp = _build_solver_input(interval=360, num_vehicles=2, start=0, end=5400)
        result = solve_schedule(inp, timeout_seconds=30)
        assert result is not None
        assert len(result.assignments) == inp.num_vehicles * inp.trips_per_vehicle

    def test_all_departures_within_time_range(self):
        inp = _build_solver_input(interval=360, num_vehicles=2, start=0, end=5400)
        result = solve_schedule(inp, timeout_seconds=30)
        assert result is not None
        max_cycle = max(inp.cycle_times)
        for a in result.assignments:
            assert a.depart_time >= inp.start_time
            assert a.depart_time + max_cycle <= inp.end_time

    def test_variant_indices_are_valid(self):
        inp = _build_solver_input(interval=360, num_vehicles=2, start=0, end=5400)
        result = solve_schedule(inp, timeout_seconds=30)
        assert result is not None
        for a in result.assignments:
            assert 0 <= a.variant_index < 8

    def test_vehicle_continuity_respected(self):
        inp = _build_solver_input(interval=360, num_vehicles=2, start=0, end=7200)
        result = solve_schedule(inp, timeout_seconds=30)
        assert result is not None
        by_vehicle: dict[int, list] = {}
        for a in result.assignments:
            by_vehicle.setdefault(a.vehicle_index, []).append(a)
        for trips in by_vehicle.values():
            trips.sort(key=lambda t: t.depart_time)
            for i in range(len(trips) - 1):
                prev, nxt = trips[i], trips[i + 1]
                cycle = inp.cycle_times[prev.variant_index]
                yard_dwell = inp.min_yard_dwells[prev.variant_index]
                assert nxt.depart_time >= prev.depart_time + cycle + yard_dwell

    def test_station_frequency_respected(self):
        inp = _build_solver_input(interval=360, num_vehicles=2, start=0, end=5400)
        result = solve_schedule(inp, timeout_seconds=30)
        assert result is not None
        for sname in ["S1", "S2", "S3"]:
            arrivals = []
            for a in result.assignments:
                var = inp.variants[a.variant_index]
                for sa in var.station_arrivals:
                    if sa.station_name == sname:
                        arrivals.append(a.depart_time + sa.arrival_offset)
            arrivals.sort()
            for i in range(len(arrivals) - 1):
                gap = arrivals[i + 1] - arrivals[i]
                assert gap <= inp.interval_seconds, (
                    f"{sname} gap {gap} > {inp.interval_seconds} "
                    f"between {arrivals[i]} and {arrivals[i + 1]}"
                )

    def test_block_no_overlap(self):
        inp = _build_solver_input(interval=360, num_vehicles=2, start=0, end=5400)
        result = solve_schedule(inp, timeout_seconds=30)
        assert result is not None
        from collections import defaultdict

        block_intervals: dict[str, list[tuple[int, int]]] = defaultdict(list)
        for a in result.assignments:
            var = inp.variants[a.variant_index]
            for bt in var.block_timings:
                enter = a.depart_time + bt.enter_offset
                exit_ = a.depart_time + bt.exit_offset
                block_intervals[bt.block_id].append((enter, exit_))

        for bid, intervals in block_intervals.items():
            intervals.sort()
            for i in range(len(intervals) - 1):
                assert intervals[i][1] <= intervals[i + 1][0], (
                    f"Block {bid} overlap: {intervals[i]} and {intervals[i + 1]}"
                )

    def test_infeasible_returns_none(self):
        """Interval=300 is infeasible because interlocking group 2 requires
        330s minimum separation, conflicting with the 300s frequency target."""
        inp = _build_solver_input(interval=10, num_vehicles=3, start=0, end=600)
        result = solve_schedule(inp, timeout_seconds=5)
        assert result is None

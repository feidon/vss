from application.schedule.model import SolverInput
from application.schedule.route_variant import compute_route_variants
from application.schedule.solver import solve_schedule
from infra.seed import (
    VEHICLE_ID_BY_NAME,
    create_blocks,
    create_connections,
    create_stations,
)


def _build_cycle_input(
    interval: int = 360,
    num_vehicles: int = 2,
    dwell: int = 30,
) -> SolverInput:
    blocks = create_blocks()
    variants = compute_route_variants(
        stations=create_stations(),
        blocks=blocks,
        connections=create_connections(),
        dwell_time_seconds=dwell,
    )

    interlocking_groups: dict[int, list] = {}
    for b in blocks:
        if b.group != 0:
            interlocking_groups.setdefault(b.group, []).append(b.id)

    cycle_times = [v.cycle_time for v in variants]
    min_yard_dwells = [v.num_blocks * 12 for v in variants]
    tile_period = max(c + y for c, y in zip(cycle_times, min_yard_dwells))

    return SolverInput(
        variants=variants,
        num_vehicles=num_vehicles,
        vehicle_ids=list(VEHICLE_ID_BY_NAME.values())[:num_vehicles],
        tile_period=tile_period,
        interval_seconds=interval,
        min_yard_dwells=min_yard_dwells,
        cycle_times=cycle_times,
        interlocking_groups=interlocking_groups,
    )


class TestSolveCycle:
    def test_returns_one_assignment_per_vehicle(self):
        inp = _build_cycle_input(interval=360, num_vehicles=2)
        result = solve_schedule(inp, timeout_seconds=30)
        assert result is not None
        assert len(result.assignments) == inp.num_vehicles

    def test_departures_within_tile_period(self):
        inp = _build_cycle_input(interval=360, num_vehicles=2)
        result = solve_schedule(inp, timeout_seconds=30)
        assert result is not None
        for a in result.assignments:
            assert 0 <= a.depart_time < inp.tile_period

    def test_variant_indices_valid(self):
        inp = _build_cycle_input(interval=360, num_vehicles=2)
        result = solve_schedule(inp, timeout_seconds=30)
        assert result is not None
        for a in result.assignments:
            assert 0 <= a.variant_index < 8

    def test_block_no_overlap_across_tiles(self):
        """Simulate 3 tiles; verify no block overlaps."""
        inp = _build_cycle_input(interval=360, num_vehicles=2)
        result = solve_schedule(inp, timeout_seconds=30)
        assert result is not None

        from collections import defaultdict

        block_intervals: dict[str, list[tuple[int, int]]] = defaultdict(list)
        for tile in range(3):
            for a in result.assignments:
                var = inp.variants[a.variant_index]
                for bt in var.block_timings:
                    enter = tile * inp.tile_period + a.depart_time + bt.enter_offset
                    exit_ = tile * inp.tile_period + a.depart_time + bt.exit_offset
                    block_intervals[bt.block_id].append((enter, exit_))

        for bid, intervals in block_intervals.items():
            intervals.sort()
            for i in range(len(intervals) - 1):
                assert intervals[i][1] <= intervals[i + 1][0], (
                    f"Block {bid} overlap: {intervals[i]} and {intervals[i + 1]}"
                )

    def test_station_frequency_across_tiles(self):
        """Simulate 3 tiles; verify all station gaps <= interval."""
        inp = _build_cycle_input(interval=360, num_vehicles=2)
        result = solve_schedule(inp, timeout_seconds=30)
        assert result is not None

        for sname in ["S1", "S2", "S3"]:
            arrivals = []
            for tile in range(3):
                for a in result.assignments:
                    var = inp.variants[a.variant_index]
                    for sa in var.station_arrivals:
                        if sa.station_name == sname:
                            arrivals.append(
                                tile * inp.tile_period
                                + a.depart_time
                                + sa.arrival_offset
                            )
            arrivals.sort()
            for i in range(len(arrivals) - 1):
                gap = arrivals[i + 1] - arrivals[i]
                assert gap <= inp.interval_seconds, (
                    f"{sname} gap {gap} > {inp.interval_seconds} "
                    f"between {arrivals[i]} and {arrivals[i + 1]}"
                )

    def test_infeasible_returns_none(self):
        inp = _build_cycle_input(interval=10, num_vehicles=3)
        result = solve_schedule(inp, timeout_seconds=5)
        assert result is None

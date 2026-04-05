from collections import defaultdict
from uuid import UUID

from application.schedule.model import SolverInput
from application.schedule.route_variant import compute_route_variants
from application.schedule.solver import solve_schedule
from infra.seed import (
    VEHICLE_ID_BY_NAME,
    create_blocks,
    create_connections,
    create_stations,
)


def _build_input(
    interval: int = 360,
    num_vehicles: int = 2,
    dwell: int = 30,
    start_time: int = 0,
    end_time: int = 3600,
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

    return SolverInput(
        variants=variants,
        num_vehicles=num_vehicles,
        vehicle_ids=list(VEHICLE_ID_BY_NAME.values())[:num_vehicles],
        start_time=start_time,
        end_time=end_time,
        interval_seconds=interval,
        interlocking_groups=interlocking_groups,
    )


class TestGreedySolver:
    def test_produces_assignments(self):
        inp = _build_input(interval=360, num_vehicles=2)
        result = solve_schedule(inp)
        assert len(result.assignments) > 0

    def test_departures_within_time_range(self):
        inp = _build_input(interval=360, num_vehicles=2)
        result = solve_schedule(inp)
        for a in result.assignments:
            assert a.depart_time >= inp.start_time
            variant = inp.variants[a.variant_index]
            assert a.depart_time + variant.cycle_time <= inp.end_time

    def test_variant_indices_valid(self):
        inp = _build_input(interval=360, num_vehicles=2)
        result = solve_schedule(inp)
        for a in result.assignments:
            assert 0 <= a.variant_index < len(inp.variants)

    def test_vehicle_indices_valid(self):
        inp = _build_input(interval=360, num_vehicles=2)
        result = solve_schedule(inp)
        for a in result.assignments:
            assert 0 <= a.vehicle_index < inp.num_vehicles

    def test_no_block_overlaps(self):
        inp = _build_input(interval=360, num_vehicles=2)
        result = solve_schedule(inp)
        block_intervals: dict[UUID, list[tuple[int, int]]] = defaultdict(list)
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

    def test_no_interlocking_overlaps(self):
        inp = _build_input(interval=360, num_vehicles=2)
        result = solve_schedule(inp)
        block_intervals: dict[UUID, list[tuple[int, int]]] = defaultdict(list)
        for a in result.assignments:
            var = inp.variants[a.variant_index]
            for bt in var.block_timings:
                enter = a.depart_time + bt.enter_offset
                exit_ = a.depart_time + bt.exit_offset
                block_intervals[bt.block_id].append((enter, exit_))

        for group_block_ids in inp.interlocking_groups.values():
            group_intervals = []
            for bid in group_block_ids:
                group_intervals.extend(block_intervals.get(bid, []))
            group_intervals.sort()
            for i in range(len(group_intervals) - 1):
                assert group_intervals[i][1] <= group_intervals[i + 1][0], (
                    f"Interlocking overlap: {group_intervals[i]} and {group_intervals[i + 1]}"
                )

    def test_tight_interval_still_produces_result(self):
        """interval=120s was infeasible with CP-SAT cyclic solver."""
        inp = _build_input(interval=120, num_vehicles=6, end_time=7200)
        result = solve_schedule(inp)
        assert len(result.assignments) > 0

    def test_empty_when_time_range_too_short(self):
        inp = _build_input(interval=360, num_vehicles=2, start_time=0, end_time=100)
        result = solve_schedule(inp)
        assert len(result.assignments) == 0

    def test_vehicle_recharge_respected(self):
        """Same vehicle's consecutive trips have enough yard dwell."""
        inp = _build_input(interval=360, num_vehicles=2, end_time=7200)
        result = solve_schedule(inp)

        by_vehicle: dict[int, list] = defaultdict(list)
        for a in result.assignments:
            by_vehicle[a.vehicle_index].append(a)

        for trips in by_vehicle.values():
            trips.sort(key=lambda a: a.depart_time)
            for i in range(len(trips) - 1):
                prev = trips[i]
                curr = trips[i + 1]
                prev_var = inp.variants[prev.variant_index]
                cycle_end = prev.depart_time + prev_var.cycle_time
                yard_dwell = prev_var.num_blocks * 12
                assert curr.depart_time >= cycle_end + yard_dwell, (
                    f"V{prev.vehicle_index}: next trip at {curr.depart_time} "
                    f"but earliest available at {cycle_end + yard_dwell}"
                )

    def test_deterministic(self):
        """Same input produces same output."""
        inp = _build_input(interval=300, num_vehicles=3, end_time=7200)
        r1 = solve_schedule(inp)
        r2 = solve_schedule(inp)
        assert len(r1.assignments) == len(r2.assignments)
        for a1, a2 in zip(r1.assignments, r2.assignments):
            assert a1.depart_time == a2.depart_time
            assert a1.variant_index == a2.variant_index
            assert a1.vehicle_index == a2.vehicle_index

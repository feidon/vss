import math
from collections import defaultdict
from uuid import UUID

from application.schedule.model import SolverInput
from application.schedule.network_layout import (
    FLEET_BUFFER,
    SECONDS_TO_RECHARGE_PER_BLOCK,
)
from application.schedule.route_variant import compute_route_variants
from application.schedule.solver import solve_schedule
from infra.seed import (
    create_blocks,
    create_connections,
    create_stations,
    create_vehicles,
)


def _build_input(
    interval: int = 360,
    dwell: int = 30,
    start_time: int = 0,
    end_time: int = 3600,
) -> SolverInput:
    """Build SolverInput with auto-computed num_vehicles (same formula as schedule service)."""
    blocks = create_blocks()
    variants = compute_route_variants(
        stations=create_stations(),
        blocks=blocks,
        connections=create_connections(),
        dwell_time_seconds=dwell,
    )

    cycle_times = [v.cycle_time for v in variants]
    min_yard_dwells = [v.num_blocks * SECONDS_TO_RECHARGE_PER_BLOCK for v in variants]
    max_turnaround = max(c + y for c, y in zip(cycle_times, min_yard_dwells))
    num_vehicles = math.ceil(max_turnaround / interval) + FLEET_BUFFER

    interlocking_groups: dict[int, list] = {}
    for b in blocks:
        if b.group != 0:
            interlocking_groups.setdefault(b.group, []).append(b.id)

    vehicle_ids = [v.id for v in create_vehicles()]
    # Extend with generated IDs if we need more than seed provides
    while len(vehicle_ids) < num_vehicles:
        from uuid import uuid4

        vehicle_ids.append(uuid4())

    return SolverInput(
        variants=variants,
        num_vehicles=num_vehicles,
        vehicle_ids=vehicle_ids[:num_vehicles],
        start_time=start_time,
        end_time=end_time,
        departure_gap_seconds=interval,
        interlocking_groups=interlocking_groups,
    )


class TestGreedySolver:
    def test_produces_assignments(self):
        inp = _build_input(interval=360)
        result = solve_schedule(inp)
        assert len(result.assignments) > 0

    def test_departures_within_time_range(self):
        inp = _build_input(interval=360)
        result = solve_schedule(inp)
        for a in result.assignments:
            assert a.depart_time >= inp.start_time
            variant = inp.variants[a.variant_index]
            assert a.depart_time + variant.cycle_time <= inp.end_time

    def test_variant_indices_valid(self):
        inp = _build_input(interval=360)
        result = solve_schedule(inp)
        for a in result.assignments:
            assert 0 <= a.variant_index < len(inp.variants)

    def test_vehicle_indices_valid(self):
        inp = _build_input(interval=360)
        result = solve_schedule(inp)
        for a in result.assignments:
            assert 0 <= a.vehicle_index < inp.num_vehicles

    def test_no_block_overlaps(self):
        inp = _build_input(interval=360)
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
        inp = _build_input(interval=360)
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
        inp = _build_input(interval=120, end_time=7200)
        result = solve_schedule(inp)
        assert len(result.assignments) > 0

    def test_empty_when_time_range_too_short(self):
        inp = _build_input(interval=360, start_time=0, end_time=100)
        result = solve_schedule(inp)
        assert len(result.assignments) == 0

    def test_vehicle_recharge_respected(self):
        """Same vehicle's consecutive trips have enough yard dwell."""
        inp = _build_input(interval=360, end_time=7200)
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
                yard_dwell = prev_var.num_blocks * SECONDS_TO_RECHARGE_PER_BLOCK
                assert curr.depart_time >= cycle_end + yard_dwell, (
                    f"V{prev.vehicle_index}: next trip at {curr.depart_time} "
                    f"but earliest available at {cycle_end + yard_dwell}"
                )

    def test_deterministic(self):
        """Same input produces same output."""
        inp = _build_input(interval=300, end_time=7200)
        r1 = solve_schedule(inp)
        r2 = solve_schedule(inp)
        assert len(r1.assignments) == len(r2.assignments)
        for a1, a2 in zip(r1.assignments, r2.assignments):
            assert a1.depart_time == a2.depart_time
            assert a1.variant_index == a2.variant_index
            assert a1.vehicle_index == a2.vehicle_index


def _collect_station_arrivals(
    inp: SolverInput,
    result,
) -> dict[str, list[int]]:
    """Collect absolute arrival times at each station from solver output."""
    arrivals: dict[str, list[int]] = defaultdict(list)
    for a in result.assignments:
        var = inp.variants[a.variant_index]
        for sa in var.station_arrivals:
            arrivals[sa.station_name].append(a.depart_time + sa.arrival_offset)
    for times in arrivals.values():
        times.sort()
    return arrivals


def _max_station_gap(inp: SolverInput, result) -> int:
    """Return the largest gap between consecutive arrivals across all stations."""
    arrivals = _collect_station_arrivals(inp, result)
    max_gap = 0
    for times in arrivals.values():
        for i in range(len(times) - 1):
            max_gap = max(max_gap, times[i + 1] - times[i])
    return max_gap


class TestStationFrequency:
    """Verify the core user requirement: a passenger at any station can
    board a vehicle within the specified interval."""

    def test_5min_interval_10h_range(self):
        """Standard case: 5-minute interval, 08:00-18:00."""
        start = 8 * 3600  # 08:00
        end = 18 * 3600  # 18:00
        interval = 300  # 5 minutes
        inp = _build_input(
            interval=interval,
            dwell=15,
            start_time=start,
            end_time=end,
        )
        result = solve_schedule(inp)

        assert len(result.assignments) > 0
        arrivals = _collect_station_arrivals(inp, result)
        for sname, times in arrivals.items():
            for i in range(len(times) - 1):
                gap = times[i + 1] - times[i]
                assert gap <= interval, (
                    f"Station {sname}: gap {gap}s > {interval}s "
                    f"between t={times[i]} and t={times[i + 1]}"
                )

    def test_5min_interval_covers_all_stations(self):
        """Every station (S1, S2, S3) is visited multiple times."""
        start = 8 * 3600
        end = 18 * 3600
        inp = _build_input(
            interval=300,
            dwell=15,
            start_time=start,
            end_time=end,
        )
        result = solve_schedule(inp)
        arrivals = _collect_station_arrivals(inp, result)

        for sname in ["S1", "S2", "S3"]:
            assert sname in arrivals, f"Station {sname} never visited"
            assert len(arrivals[sname]) > 10, (
                f"Station {sname} only visited {len(arrivals[sname])} times in 10h"
            )

    def test_150s_interval_perfect_frequency(self):
        """150s is the shortest interval that achieves perfect frequency
        with default 30s block traversal times — no n*150 falls inside
        any interlocking return window."""
        interval = 150
        inp = _build_input(
            interval=interval,
            dwell=15,
            start_time=0,
            end_time=7200,
        )
        result = solve_schedule(inp)
        assert len(result.assignments) > 0

        arrivals = _collect_station_arrivals(inp, result)
        for sname, times in arrivals.items():
            for i in range(len(times) - 1):
                gap = times[i + 1] - times[i]
                assert gap <= interval, (
                    f"Station {sname}: gap {gap}s > {interval}s "
                    f"between t={times[i]} and t={times[i + 1]}"
                )

    def test_2min_interval_produces_trips_despite_bottleneck(self):
        """Tight interval (120s) was infeasible with CP-SAT. Greedy produces
        the best achievable schedule, but the yard interlocking physically
        limits throughput — gaps at S3 may reach the cycle time."""
        interval = 120
        inp = _build_input(
            interval=interval,
            dwell=15,
            start_time=0,
            end_time=3600,
        )
        result = solve_schedule(inp)
        assert len(result.assignments) > 10  # should get ~14 trips in 1h

        max_gap = _max_station_gap(inp, result)
        max_cycle = max(v.cycle_time for v in inp.variants)
        assert max_gap <= max_cycle, (
            f"Max station gap {max_gap}s exceeds cycle time {max_cycle}s"
        )

    def test_3min_interval_mostly_within_target(self):
        """3-minute interval over 2 hours. The yard interlocking may force
        occasional gaps slightly above 180s (by ~15s) when a returning
        vehicle blocks the next departure."""
        interval = 180
        inp = _build_input(
            interval=interval,
            dwell=15,
            start_time=0,
            end_time=7200,
        )
        result = solve_schedule(inp)
        assert len(result.assignments) > 0

        max_gap = _max_station_gap(inp, result)
        # Allow up to one block traversal time (30s) of slack
        # beyond the target interval for yard bottleneck shifts
        assert max_gap <= interval + 30, (
            f"Max station gap {max_gap}s exceeds {interval + 30}s"
        )

    def test_60s_interval(self):
        """1-minute interval — very tight. Network can't sustain it,
        but solver should produce trips without crashing."""
        interval = 60
        inp = _build_input(interval=interval, dwell=15, start_time=0, end_time=3600)
        result = solve_schedule(inp)
        assert len(result.assignments) > 0

        max_gap = _max_station_gap(inp, result)
        max_cycle = max(v.cycle_time for v in inp.variants)
        assert max_gap <= max_cycle, (
            f"Max station gap {max_gap}s exceeds cycle time {max_cycle}s"
        )

    def test_90s_interval(self):
        """1.5-minute interval over 2 hours."""
        interval = 90
        inp = _build_input(interval=interval, dwell=15, start_time=0, end_time=7200)
        result = solve_schedule(inp)
        assert len(result.assignments) > 0

        max_gap = _max_station_gap(inp, result)
        max_cycle = max(v.cycle_time for v in inp.variants)
        assert max_gap <= max_cycle, (
            f"Max station gap {max_gap}s exceeds cycle time {max_cycle}s"
        )

    def test_all_vehicles_used_over_long_range(self):
        """Over a 10h range, all provisioned vehicles should serve trips."""
        start = 8 * 3600
        end = 18 * 3600
        inp = _build_input(
            interval=300,
            dwell=15,
            start_time=start,
            end_time=end,
        )
        result = solve_schedule(inp)

        vehicles_used = {a.vehicle_index for a in result.assignments}
        assert vehicles_used == set(range(inp.num_vehicles)), (
            f"Expected vehicles {set(range(inp.num_vehicles))}, got {vehicles_used}"
        )

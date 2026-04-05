"""CP-SAT constraint solver for automatic schedule generation.

Pure function - no I/O, no async, no domain objects.
Takes SolverInput, returns SolverOutput or None (infeasible).
"""

from __future__ import annotations

from collections import defaultdict
from uuid import UUID

from ortools.sat.python import cp_model

from application.schedule.model import (
    SolverInput,
    SolverOutput,
    TripAssignment,
)


def solve_schedule(
    inp: SolverInput,
    *,
    timeout_seconds: int = 60,
) -> SolverOutput | None:
    """Solve the vehicle scheduling problem using CP-SAT.

    Decision variables per trip:
        depart_time  – IntVar in [start_time, end_time - max_cycle]
        s1_out       – BoolVar (0=P1A, 1=P1B)
        s3           – BoolVar (0=P3A, 1=P3B)
        s1_ret       – BoolVar (0=P1A, 1=P1B)
        variant_idx  – IntVar derived as s1_out*4 + s3*2 + s1_ret

    Constraints:
        C1 – Block occupancy (no overlap on same block)
        C2 – Interlocking (no overlap on blocks in same group)
        C3 – Vehicle continuity (consecutive trips spaced by cycle + yard dwell)
        C5 – Station frequency (consecutive arrivals at each station within interval)
        C6 – Time range (departures within allowed window)
    """
    model = cp_model.CpModel()
    total_trips = inp.num_vehicles * inp.trips_per_vehicle
    max_cycle = max(inp.cycle_times)
    time_horizon = inp.end_time + max_cycle

    # ── Decision variables ──────────────────────────────────────

    depart: list[cp_model.IntVar] = []
    variant_idx: list[cp_model.IntVar] = []

    # Pre-create is_variant[s][v] booleans - shared across all constraints
    is_variant: list[list[cp_model.IntVar]] = []

    for s in range(total_trips):
        # C6: departures within [start_time, end_time - max_cycle]
        d = model.new_int_var(inp.start_time, inp.end_time - max_cycle, f"depart_{s}")
        depart.append(d)

        b_s1_out = model.new_bool_var(f"s1_out_{s}")
        b_s3 = model.new_bool_var(f"s3_{s}")
        b_s1_ret = model.new_bool_var(f"s1_ret_{s}")

        vi = model.new_int_var(0, 7, f"variant_{s}")
        model.add(vi == b_s1_out * 4 + b_s3 * 2 + b_s1_ret)
        variant_idx.append(vi)

        # Create exactly-one booleans for each variant
        bools = [model.new_bool_var(f"is_v{v}_t{s}") for v in range(8)]
        for v in range(8):
            model.add(vi == v).only_enforce_if(bools[v])
            model.add(vi != v).only_enforce_if(~bools[v])
        is_variant.append(bools)

    # ── Precompute block-to-variant timing lookup ───────────────

    block_occurrences: dict[UUID, list[tuple[int, int, int]]] = defaultdict(list)
    for var in inp.variants:
        for bt in var.block_timings:
            block_occurrences[bt.block_id].append(
                (var.index, bt.enter_offset, bt.exit_offset)
            )

    # Identify which blocks are in interlocking groups (C2 subsumes C1)
    group_block_set: set[UUID] = set()
    for gblocks in inp.interlocking_groups.values():
        group_block_set.update(gblocks)

    # Helper to create optional interval for a (trip, block, variant) combo
    def _make_optional_interval(
        s: int,
        var_i: int,
        enter_off: int,
        exit_off: int,
        prefix: str,
    ) -> cp_model.IntervalVar:
        lit = is_variant[s][var_i]
        duration = exit_off - enter_off
        start = model.new_int_var(
            inp.start_time + enter_off,
            inp.end_time - max_cycle + enter_off,
            f"{prefix}_start_t{s}_v{var_i}",
        )
        model.add(start == depart[s] + enter_off).only_enforce_if(lit)
        return model.new_optional_fixed_size_interval_var(
            start, duration, lit, f"{prefix}_iv_t{s}_v{var_i}"
        )

    # ── C1 + C2: Block and interlocking constraints ─────────────
    # For interlocking groups: one NoOverlap per group (all blocks in group).
    # For non-group blocks: one NoOverlap per block.
    # This avoids duplicating constraints for interlocking-group blocks.

    # C1: per-block NoOverlap for blocks NOT in any interlocking group
    for bid, occs in block_occurrences.items():
        if bid in group_block_set:
            continue
        intervals: list[cp_model.IntervalVar] = []
        for s in range(total_trips):
            for var_i, enter_off, exit_off in occs:
                intervals.append(
                    _make_optional_interval(s, var_i, enter_off, exit_off, f"b_{bid}")
                )
        if len(intervals) > 1:
            model.add_no_overlap(intervals)

    # C2: per-group NoOverlap (subsumes C1 for these blocks)
    for group_id, group_block_ids in inp.interlocking_groups.items():
        group_intervals: list[cp_model.IntervalVar] = []
        for bid in group_block_ids:
            for s in range(total_trips):
                for var_i, enter_off, exit_off in block_occurrences.get(bid, []):
                    group_intervals.append(
                        _make_optional_interval(
                            s,
                            var_i,
                            enter_off,
                            exit_off,
                            f"g{group_id}_{bid}",
                        )
                    )
        if len(group_intervals) > 1:
            model.add_no_overlap(group_intervals)

    # ── C3: Vehicle continuity ──────────────────────────────────

    for v in range(inp.num_vehicles):
        vehicle_trips = [
            v * inp.trips_per_vehicle + t for t in range(inp.trips_per_vehicle)
        ]

        for i in range(len(vehicle_trips) - 1):
            s_prev = vehicle_trips[i]
            s_next = vehicle_trips[i + 1]

            cycle_var = model.new_int_var(
                min(inp.cycle_times),
                max(inp.cycle_times),
                f"cycle_{s_prev}",
            )
            model.add_element(variant_idx[s_prev], inp.cycle_times, cycle_var)

            yd_var = model.new_int_var(
                min(inp.min_yard_dwells),
                max(inp.min_yard_dwells),
                f"yd_{s_prev}",
            )
            model.add_element(variant_idx[s_prev], inp.min_yard_dwells, yd_var)

            model.add(depart[s_next] >= depart[s_prev] + cycle_var + yd_var)

        # Symmetry breaking: order trips within a vehicle
        for i in range(len(vehicle_trips) - 1):
            model.add(depart[vehicle_trips[i]] < depart[vehicle_trips[i + 1]])

    # ── C5: Station frequency ───────────────────────────────────

    station_names = ["S1", "S2", "S3"]
    for sname in station_names:
        visits_per_variant: list[list[int]] = []
        for var in inp.variants:
            hits = [sa for sa in var.station_arrivals if sa.station_name == sname]
            visits_per_variant.append([h.arrival_offset for h in hits])

        num_visits = len(visits_per_variant[0])

        arrivals: list[cp_model.IntVar] = []
        for visit_idx in range(num_visits):
            offsets = [visits_per_variant[v][visit_idx] for v in range(8)]
            for s in range(total_trips):
                off_var = model.new_int_var(
                    min(offsets),
                    max(offsets),
                    f"off_{sname}_v{visit_idx}_t{s}",
                )
                model.add_element(variant_idx[s], offsets, off_var)
                arr = model.new_int_var(
                    inp.start_time,
                    time_horizon,
                    f"arr_{sname}_v{visit_idx}_t{s}",
                )
                model.add(arr == depart[s] + off_var)
                arrivals.append(arr)

        n = len(arrivals)
        if n <= 1:
            continue

        sorted_arr = [
            model.new_int_var(inp.start_time, time_horizon, f"sorted_{sname}_{k}")
            for k in range(n)
        ]
        pos = [model.new_int_var(0, n - 1, f"pos_{sname}_{i}") for i in range(n)]
        model.add_all_different(pos)

        for i in range(n):
            model.add_element(pos[i], sorted_arr, arrivals[i])

        for k in range(n - 1):
            model.add(sorted_arr[k] <= sorted_arr[k + 1])
            model.add(sorted_arr[k + 1] - sorted_arr[k] <= inp.interval_seconds)

    # ── Solve ───────────────────────────────────────────────────

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = timeout_seconds
    solver.parameters.num_workers = 8

    status = solver.solve(model)

    if status not in (cp_model.FEASIBLE, cp_model.OPTIMAL):
        return None

    assignments: list[TripAssignment] = []
    for s in range(total_trips):
        vehicle_index = s // inp.trips_per_vehicle
        trip_index = s % inp.trips_per_vehicle
        assignments.append(
            TripAssignment(
                vehicle_index=vehicle_index,
                trip_index=trip_index,
                depart_time=solver.value(depart[s]),
                variant_index=solver.value(variant_idx[s]),
            )
        )

    return SolverOutput(assignments=assignments)

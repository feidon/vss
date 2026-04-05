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
    """Solve one cycle of the vehicle scheduling problem using CP-SAT.

    Produces exactly num_vehicles trip assignments (one per vehicle).
    Departures are 0-based offsets within [0, tile_period).
    Ghost intervals shifted by +tile_period enforce wraparound safety
    so the solution can be tiled without conflicts.

    Constraints:
        C1 - Block occupancy (no overlap on same block, incl. wraparound ghosts)
        C2 - Interlocking (no overlap in same group, incl. wraparound ghosts)
        C5 - Station frequency (consecutive arrivals within interval + wraparound)
        C6 - Departures within [0, tile_period)
    """
    model = cp_model.CpModel()
    num_trips = inp.num_vehicles
    P = inp.tile_period

    # -- Decision variables --------------------------------------------------

    depart: list[cp_model.IntVar] = []
    variant_idx: list[cp_model.IntVar] = []
    is_variant: list[list[cp_model.IntVar]] = []

    for s in range(num_trips):
        d = model.new_int_var(0, P - 1, f"depart_{s}")
        depart.append(d)

        b_s1_out = model.new_bool_var(f"s1_out_{s}")
        b_s3 = model.new_bool_var(f"s3_{s}")
        b_s1_ret = model.new_bool_var(f"s1_ret_{s}")

        vi = model.new_int_var(0, 7, f"variant_{s}")
        model.add(vi == b_s1_out * 4 + b_s3 * 2 + b_s1_ret)
        variant_idx.append(vi)

        bools = [model.new_bool_var(f"is_v{v}_t{s}") for v in range(8)]
        for v in range(8):
            model.add(vi == v).only_enforce_if(bools[v])
            model.add(vi != v).only_enforce_if(~bools[v])
        is_variant.append(bools)

    # -- Block-to-variant timing lookup --------------------------------------

    block_occurrences: dict[UUID, list[tuple[int, int, int]]] = defaultdict(list)
    for var in inp.variants:
        for bt in var.block_timings:
            block_occurrences[bt.block_id].append(
                (var.index, bt.enter_offset, bt.exit_offset)
            )

    group_block_set: set[UUID] = set()
    for gblocks in inp.interlocking_groups.values():
        group_block_set.update(gblocks)

    # -- Interval helpers ----------------------------------------------------

    def _make_interval(
        s: int,
        var_i: int,
        enter_off: int,
        exit_off: int,
        prefix: str,
        shift: int = 0,
    ) -> cp_model.IntervalVar:
        """Create optional interval at depart[s] + shift + enter_off."""
        lit = is_variant[s][var_i]
        duration = exit_off - enter_off
        lo = shift + enter_off
        hi = P - 1 + shift + enter_off
        start = model.new_int_var(lo, hi, f"{prefix}_st_t{s}_v{var_i}")
        model.add(start == depart[s] + shift + enter_off).only_enforce_if(lit)
        return model.new_optional_fixed_size_interval_var(
            start, duration, lit, f"{prefix}_iv_t{s}_v{var_i}"
        )

    def _block_intervals(
        bid: UUID,
        occs: list[tuple[int, int, int]],
        prefix: str,
    ) -> list[cp_model.IntervalVar]:
        """Real + ghost intervals for one block across all trips."""
        intervals: list[cp_model.IntervalVar] = []
        for s in range(num_trips):
            for var_i, enter_off, exit_off in occs:
                intervals.append(_make_interval(s, var_i, enter_off, exit_off, prefix))
                intervals.append(
                    _make_interval(
                        s, var_i, enter_off, exit_off, f"g_{prefix}", shift=P
                    )
                )
        return intervals

    # -- C1: Block occupancy (non-interlocking) + wraparound -----------------

    for bid, occs in block_occurrences.items():
        if bid in group_block_set:
            continue
        intervals = _block_intervals(bid, occs, f"b_{bid}")
        if len(intervals) > 1:
            model.add_no_overlap(intervals)

    # -- C2: Interlocking groups + wraparound --------------------------------

    for group_id, group_block_ids in inp.interlocking_groups.items():
        group_intervals: list[cp_model.IntervalVar] = []
        for bid in group_block_ids:
            occs = block_occurrences.get(bid, [])
            group_intervals.extend(_block_intervals(bid, occs, f"g{group_id}_{bid}"))
        if len(group_intervals) > 1:
            model.add_no_overlap(group_intervals)

    # -- C5: Station frequency + wraparound ----------------------------------

    station_names = ["S1", "S2", "S3"]
    for sname in station_names:
        visits_per_variant: list[list[int]] = []
        for var in inp.variants:
            hits = [sa for sa in var.station_arrivals if sa.station_name == sname]
            visits_per_variant.append([h.arrival_offset for h in hits])

        num_visits = len(visits_per_variant[0])
        time_horizon = 2 * P + max(
            off for offsets in visits_per_variant for off in offsets
        )

        arrivals: list[cp_model.IntVar] = []
        for visit_idx in range(num_visits):
            offsets = [visits_per_variant[v][visit_idx] for v in range(8)]
            for s in range(num_trips):
                off_var = model.new_int_var(
                    min(offsets),
                    max(offsets),
                    f"off_{sname}_v{visit_idx}_t{s}",
                )
                model.add_element(variant_idx[s], offsets, off_var)
                arr = model.new_int_var(
                    0,
                    time_horizon,
                    f"arr_{sname}_v{visit_idx}_t{s}",
                )
                model.add(arr == depart[s] + off_var)
                arrivals.append(arr)

        n = len(arrivals)
        if n <= 1:
            continue

        sorted_arr = [
            model.new_int_var(0, time_horizon, f"sorted_{sname}_{k}") for k in range(n)
        ]
        pos = [model.new_int_var(0, n - 1, f"pos_{sname}_{i}") for i in range(n)]
        model.add_all_different(pos)

        for i in range(n):
            model.add_element(pos[i], sorted_arr, arrivals[i])

        for k in range(n - 1):
            model.add(sorted_arr[k] <= sorted_arr[k + 1])
            model.add(sorted_arr[k + 1] - sorted_arr[k] <= inp.interval_seconds)

        # Wraparound: gap from last arrival to first arrival of next tile
        # (first_of_next_tile) - last_of_this_tile <= interval
        # (sorted_arr[0] + P) - sorted_arr[n-1] <= interval
        model.add(sorted_arr[0] + P - sorted_arr[n - 1] <= inp.interval_seconds)

    # -- Solve ---------------------------------------------------------------

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = timeout_seconds
    solver.parameters.num_workers = 8

    status = solver.solve(model)

    if status not in (cp_model.FEASIBLE, cp_model.OPTIMAL):
        return None

    assignments: list[TripAssignment] = []
    for s in range(num_trips):
        assignments.append(
            TripAssignment(
                vehicle_index=s,
                trip_index=0,
                depart_time=solver.value(depart[s]),
                variant_index=solver.value(variant_idx[s]),
            )
        )

    return SolverOutput(assignments=assignments)

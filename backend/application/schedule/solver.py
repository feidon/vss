"""Greedy sequential dispatch solver for automatic schedule generation.

Pure function — no I/O, no async, no domain objects.
Takes SolverInput, returns SolverOutput (possibly with empty assignments).
"""

from __future__ import annotations

import bisect
from collections import defaultdict
from uuid import UUID

from application.schedule.model import (
    RouteVariant,
    SolverInput,
    SolverOutput,
    TripAssignment,
)
from application.schedule.network_layout import SECONDS_TO_RECHARGE_PER_BLOCK


def solve_schedule(inp: SolverInput) -> SolverOutput:
    """Place trips one at a time in temporal order.

    For each departure slot, pick the first available vehicle
    (tie-break: lowest index) and the first route variant (index
    order 0-7) that has no block or interlocking conflicts with
    already-placed trips.
    """
    occupancies: dict[UUID, list[tuple[int, int]]] = defaultdict(list)
    vehicle_available = {i: inp.start_time for i in range(inp.num_vehicles)}
    assignments: list[TripAssignment] = []

    group_for_block = _build_group_lookup(inp.interlocking_groups)
    min_cycle = min(v.cycle_time for v in inp.variants)

    next_desired = inp.start_time
    while next_desired + min_cycle <= inp.end_time:
        vehicle = min(vehicle_available, key=lambda v: (vehicle_available[v], v))
        depart = max(vehicle_available[vehicle], next_desired)

        placed = False
        earliest_conflict_end = next_desired
        for variant in inp.variants:
            if depart + variant.cycle_time > inp.end_time:
                continue
            conflict_end = _find_conflict(
                depart, variant, occupancies, inp.interlocking_groups, group_for_block
            )
            if conflict_end is None:
                _record_occupancies(depart, variant, occupancies)
                yard_dwell = variant.num_blocks * SECONDS_TO_RECHARGE_PER_BLOCK
                vehicle_available[vehicle] = depart + variant.cycle_time + yard_dwell
                assignments.append(
                    TripAssignment(
                        vehicle_index=vehicle,
                        depart_time=depart,
                        variant_index=variant.index,
                    )
                )
                next_desired = depart + inp.departure_gap_seconds
                placed = True
                break
            earliest_conflict_end = max(earliest_conflict_end, conflict_end)

        if not placed:
            if earliest_conflict_end <= next_desired:
                break  # stuck — no progress possible
            next_desired = earliest_conflict_end

    return SolverOutput(assignments=assignments)


def _build_group_lookup(
    interlocking_groups: dict[int, list[UUID]],
) -> dict[UUID, int]:
    """Map each block_id to its interlocking group_id (0 if none)."""
    lookup: dict[UUID, int] = {}
    for group_id, block_ids in interlocking_groups.items():
        for bid in block_ids:
            lookup[bid] = group_id
    return lookup


def _find_conflict(
    depart: int,
    variant: RouteVariant,
    occupancies: dict[UUID, list[tuple[int, int]]],
    interlocking_groups: dict[int, list[UUID]],
    group_for_block: dict[UUID, int],
) -> int | None:
    """Return the earliest valid departure time that avoids the conflict, or None.

    When a block at enter_offset conflicts with an existing occupancy ending
    at conflict_exit, the vehicle doesn't need the block until enter_offset
    seconds after departure. So the earliest safe departure = conflict_exit - enter_offset.
    """
    for bt in variant.block_timings:
        enter = depart + bt.enter_offset
        exit_ = depart + bt.exit_offset

        # Check same block
        conflict_end = _check_overlap(enter, exit_, occupancies.get(bt.block_id, []))
        if conflict_end is not None:
            return conflict_end - bt.enter_offset

        # Check interlocking group peers
        group_id = group_for_block.get(bt.block_id)
        if group_id is not None:
            for peer_bid in interlocking_groups[group_id]:
                if peer_bid == bt.block_id:
                    continue
                conflict_end = _check_overlap(
                    enter, exit_, occupancies.get(peer_bid, [])
                )
                if conflict_end is not None:
                    return conflict_end - bt.enter_offset

    return None


def _check_overlap(
    enter: int, exit_: int, existing: list[tuple[int, int]]
) -> int | None:
    """Return the exit time of the first overlapping occupancy, or None.

    ``existing`` is kept sorted by enter time. We break early as soon as
    an occupancy starts at or after our requested exit — no later
    occupancy can overlap.
    """
    for ex_enter, ex_exit in existing:
        if ex_enter >= exit_:
            break
        if ex_exit > enter:
            return ex_exit
    return None


def _record_occupancies(
    depart: int, variant: RouteVariant, occupancies: dict[UUID, list[tuple[int, int]]]
) -> None:
    for bt in variant.block_timings:
        bisect.insort(
            occupancies[bt.block_id],
            (depart + bt.enter_offset, depart + bt.exit_offset),
        )

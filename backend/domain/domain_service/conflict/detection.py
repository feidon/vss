from __future__ import annotations

from dataclasses import replace
from uuid import UUID

from domain.vehicle.model import Vehicle

from domain.domain_service.conflict.model import (
    BlockConflict,
    BlockOccupancy,
    BlockTraversal,
    ChargeStop,
    GroupOccupancy,
    InsufficientChargeConflict,
    InterlockingConflict,
    LowBatteryConflict,
    ServiceEndpoints,
    ServiceWindow,
    Timed,
    VehicleConflict,
)


def find_time_overlaps[T: Timed](entries: list[T]) -> list[tuple[T, T]]:
    """Find all pairs with overlapping time windows.

    Sweep-line algorithm: sort by arrival, break inner loop
    when next arrival >= current departure.
    """
    sorted_entries = sorted(entries, key=lambda x: x.arrival)
    pairs: list[tuple[T, T]] = []

    for i in range(len(sorted_entries)):
        dep_i = sorted_entries[i].departure
        for j in range(i + 1, len(sorted_entries)):
            if sorted_entries[j].arrival >= dep_i:
                break
            pairs.append((sorted_entries[i], sorted_entries[j]))

    return pairs


def detect_time_overlap_conflicts(
    vehicle_id: UUID,
    windows: list[ServiceWindow],
) -> list[VehicleConflict]:
    conflicts: list[VehicleConflict] = []
    for i in range(len(windows)):
        for j in range(i + 1, len(windows)):
            prev, curr = windows[i], windows[j]
            if curr.start >= prev.end:
                break
            conflicts.append(VehicleConflict(
                vehicle_id, prev.service_id, curr.service_id,
                "Overlapping time windows",
            ))
    return conflicts


def detect_location_discontinuity_conflicts(
    vehicle_id: UUID,
    endpoints: list[ServiceEndpoints],
) -> list[VehicleConflict]:
    conflicts: list[VehicleConflict] = []
    for i in range(1, len(endpoints)):
        prev, curr = endpoints[i - 1], endpoints[i]
        if curr.first_node_id != prev.last_node_id:
            conflicts.append(VehicleConflict(
                vehicle_id, prev.service_id, curr.service_id,
                "Location discontinuity",
            ))
    return conflicts


def detect_block_conflicts(
    by_block: dict[UUID, list[BlockOccupancy]],
) -> list[BlockConflict]:
    conflicts: list[BlockConflict] = []
    for block_id, occupancies in by_block.items():
        for a, b in find_time_overlaps(occupancies):
            conflicts.append(BlockConflict.from_overlap(block_id, a, b))
    return conflicts


def detect_interlocking_conflicts(
    by_group: dict[int, list[GroupOccupancy]],
) -> list[InterlockingConflict]:
    """Detect different blocks in the same interlocking group
    occupied by different services at overlapping times."""
    conflicts: list[InterlockingConflict] = []
    for group, occupancies in by_group.items():
        if group == 0:
            continue  # group 0 means "no interlocking group"
        for a, b in find_time_overlaps(occupancies):
            if a.block_id == b.block_id:
                continue  # already caught by block conflict detection
            conflicts.append(InterlockingConflict.from_overlap(group, a, b))
    return conflicts


def detect_battery_conflicts(
    vehicle: Vehicle,
    steps: list[ChargeStop | BlockTraversal],
) -> tuple[list[LowBatteryConflict], list[InsufficientChargeConflict]]:
    low_battery: list[LowBatteryConflict] = []
    insufficient_charge: list[InsufficientChargeConflict] = []

    if not steps:
        return (low_battery, insufficient_charge)

    sim = replace(vehicle)

    for step in steps:
        match step:
            case ChargeStop():
                sim.charge(step.charge_seconds)
                if not sim.can_depart():
                    insufficient_charge.append(InsufficientChargeConflict(service_id=step.service_id))
                    break
            case BlockTraversal():
                sim.traverse_block()
                if sim.is_battery_critical():
                    low_battery.append(LowBatteryConflict(service_id=step.service_id))
                    break

    return (low_battery, insufficient_charge)

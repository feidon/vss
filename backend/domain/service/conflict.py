from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Protocol
from uuid import UUID

from domain.network.model import NodeType
from domain.shared.types import EpochSeconds
from domain.vehicle.model import Vehicle
from domain.block.model import Block
from domain.service.model import Service


# ── Value Objects ────────────────────────────────────────────


@dataclass(frozen=True)
class VehicleConflict:
    vehicle_id: UUID
    service_a_id: int
    service_b_id: int
    reason: str


@dataclass(frozen=True)
class BlockConflict:
    block_id: UUID
    service_a_id: int
    service_b_id: int
    overlap_start: int
    overlap_end: int


@dataclass(frozen=True)
class InterlockingConflict:
    group: int
    block_a_id: UUID
    block_b_id: UUID
    service_a_id: int
    service_b_id: int
    overlap_start: int
    overlap_end: int

@dataclass(frozen=True)
class LowBatteryConflict:
    service_id: int

@dataclass(frozen=True)
class InsufficientChargeConflict:
    service_a_id: int
    service_b_id: int

@dataclass(frozen=True)
class ServiceConflicts:
    vehicle_conflicts: list[VehicleConflict]
    block_conflicts: list[BlockConflict]
    interlocking_conflicts: list[InterlockingConflict]
    low_battery_conflicts: list[LowBatteryConflict] = field(default_factory=list)
    insufficient_charge_conflicts: list[InsufficientChargeConflict] = field(default_factory=list)

    @property
    def has_conflicts(self) -> bool:
        return bool(
            self.vehicle_conflicts
            or self.block_conflicts
            or self.interlocking_conflicts
            or self.low_battery_conflicts
            or self.insufficient_charge_conflicts
        )


# ── Private value objects ───────────────────────────────────


class _Timed(Protocol):
    arrival: EpochSeconds
    departure: EpochSeconds


@dataclass(frozen=True)
class _ServiceWindow:
    service_id: int
    start: EpochSeconds
    end: EpochSeconds
    first_node_id: UUID
    last_node_id: UUID


@dataclass(frozen=True)
class _BlockOccupancy:
    service_id: int
    arrival: EpochSeconds
    departure: EpochSeconds


@dataclass(frozen=True)
class _GroupOccupancy:
    service_id: int
    block_id: UUID
    arrival: EpochSeconds
    departure: EpochSeconds


@dataclass(frozen=True)
class _BatterySimEntry:
    service_id: int
    block_count: int
    start: EpochSeconds
    end: EpochSeconds
    ends_at_yard: bool


# ── Public API ──────────────────────────────────────────────


def detect_conflicts(
    candidate: Service,
    other_services: list[Service],
    blocks: list[Block],
    vehicles: list[Vehicle] | None = None,
) -> ServiceConflicts:
    """Check all conflicts for a candidate service against other services."""
    all_services = [s for s in other_services if s.id != candidate.id]
    all_services.append(candidate)

    windows = _build_service_windows(candidate.vehicle_id, all_services)
    block_occupancies = _build_block_occupancies(all_services, blocks)
    group_occupancies = _build_group_occupancies(all_services, blocks)

    low_battery: list[LowBatteryConflict] = []
    insufficient_charge: list[InsufficientChargeConflict] = []
    if vehicles:
        vehicle_by_id = {v.id: v for v in vehicles}
        candidate_vehicle = vehicle_by_id.get(candidate.vehicle_id)
        if candidate_vehicle is not None:
            battery_entries = _build_battery_entries(
                candidate_vehicle.id, all_services,
            )
            low_battery, insufficient_charge = _detect_battery_conflicts(
                candidate_vehicle.battery, battery_entries,
            )

    return ServiceConflicts(
        vehicle_conflicts=_detect_vehicle_conflicts(candidate.vehicle_id, windows),
        block_conflicts=_detect_block_conflicts(block_occupancies),
        interlocking_conflicts=_detect_interlocking_conflicts(group_occupancies),
        low_battery_conflicts=low_battery,
        insufficient_charge_conflicts=insufficient_charge,
    )


# ── Data preparation ───────────────────────────────────────


def _build_service_windows(
    vehicle_id: UUID,
    services: list[Service],
) -> list[_ServiceWindow]:
    windows: list[_ServiceWindow] = []
    for svc in services:
        if svc.vehicle_id != vehicle_id or not svc.timetable:
            continue
        entries = sorted(svc.timetable, key=lambda e: e.order)
        windows.append(_ServiceWindow(
            service_id=svc.id,
            start=min(e.arrival for e in entries),
            end=max(e.departure for e in entries),
            first_node_id=entries[0].node_id,
            last_node_id=entries[-1].node_id,
        ))
    windows.sort(key=lambda w: w.start)
    return windows


def _build_block_occupancies(
    services: list[Service],
    blocks: list[Block],
) -> dict[UUID, list[_BlockOccupancy]]:
    block_ids = {b.id for b in blocks}
    by_block: dict[UUID, list[_BlockOccupancy]] = defaultdict(list)
    for svc in services:
        for entry in svc.timetable:
            if entry.node_id in block_ids:
                by_block[entry.node_id].append(
                    _BlockOccupancy(svc.id, entry.arrival, entry.departure),
                )
    return by_block


def _build_group_occupancies(
    services: list[Service],
    blocks: list[Block],
) -> dict[int, list[_GroupOccupancy]]:
    block_by_id = {b.id: b for b in blocks}
    by_group: dict[int, list[_GroupOccupancy]] = defaultdict(list)
    for svc in services:
        for entry in svc.timetable:
            block = block_by_id.get(entry.node_id)
            if block is not None:
                by_group[block.group].append(
                    _GroupOccupancy(svc.id, block.id, entry.arrival, entry.departure),
                )
    return by_group


def _build_battery_entries(
    vehicle_id: UUID,
    services: list[Service],
) -> list[_BatterySimEntry]:
    entries: list[_BatterySimEntry] = []
    for service in services:
        if service.vehicle_id != vehicle_id:
            continue
        timetable = sorted(service.timetable, key=lambda t: t.order)
        if not timetable:
            continue
        entries.append(_BatterySimEntry(
            service_id=service.id,
            block_count=len([n for n in service.path if n.type == NodeType.BLOCK]),
            start=timetable[0].arrival,
            end=timetable[-1].departure,
            ends_at_yard=service.path[-1].type == NodeType.YARD if service.path else False,
        ))
    entries.sort(key=lambda e: e.start)
    return entries


# ── Detection logic ─────────────────────────────────────────


def _find_time_overlaps[T: _Timed](entries: list[T]) -> list[tuple[T, T]]:
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


def _detect_vehicle_conflicts(
    vehicle_id: UUID,
    windows: list[_ServiceWindow],
) -> list[VehicleConflict]:
    conflicts: list[VehicleConflict] = []

    # Overlap detection
    for i in range(len(windows)):
        for j in range(i + 1, len(windows)):
            prev, curr = windows[i], windows[j]
            if curr.start >= prev.end:
                break
            conflicts.append(VehicleConflict(
                vehicle_id, prev.service_id, curr.service_id,
                "Overlapping time windows",
            ))

    # Location discontinuity
    for i in range(1, len(windows)):
        prev, curr = windows[i - 1], windows[i]
        if curr.first_node_id != prev.last_node_id:
            conflicts.append(VehicleConflict(
                vehicle_id, prev.service_id, curr.service_id,
                "Location discontinuity",
            ))

    return conflicts


def _detect_block_conflicts(
    by_block: dict[UUID, list[_BlockOccupancy]],
) -> list[BlockConflict]:
    conflicts: list[BlockConflict] = []
    for block_id, occupancies in by_block.items():
        for a, b in _find_time_overlaps(occupancies):
            conflicts.append(BlockConflict(
                block_id=block_id,
                service_a_id=a.service_id,
                service_b_id=b.service_id,
                overlap_start=b.arrival,
                overlap_end=a.departure,
            ))
    return conflicts


def _detect_interlocking_conflicts(
    by_group: dict[int, list[_GroupOccupancy]],
) -> list[InterlockingConflict]:
    """Detect different blocks in the same interlocking group
    occupied by different services at overlapping times."""
    conflicts: list[InterlockingConflict] = []
    for group, occupancies in by_group.items():
        if group == 0:
            continue  # group 0 means "no interlocking group"
        for a, b in _find_time_overlaps(occupancies):
            if a.block_id == b.block_id:
                continue  # already caught by block conflict detection
            conflicts.append(InterlockingConflict(
                group=group,
                block_a_id=a.block_id,
                block_b_id=b.block_id,
                service_a_id=a.service_id,
                service_b_id=b.service_id,
                overlap_start=b.arrival,
                overlap_end=a.departure,
            ))
    return conflicts


def _detect_battery_conflicts(
    initial_battery: int,
    entries: list[_BatterySimEntry],
) -> tuple[list[LowBatteryConflict], list[InsufficientChargeConflict]]:
    low_battery: list[LowBatteryConflict] = []
    insufficient_charge: list[InsufficientChargeConflict] = []

    if not entries:
        return (low_battery, insufficient_charge)

    sim = Vehicle(id=UUID(int=0), name="", battery=initial_battery)

    prev_end = entries[0].start
    prev_service_id = entries[0].service_id
    prev_ends_at_yard = True  # vehicle starts at the Yard
    for entry in entries:
        if prev_ends_at_yard:
            sim.charge(entry.start - prev_end)
        if not sim.can_depart():
            insufficient_charge.append(InsufficientChargeConflict(
                service_a_id=prev_service_id,
                service_b_id=entry.service_id,
            ))
            break

        sim.consume_battery(entry.block_count)
        if sim.is_battery_critical():
            low_battery.append(LowBatteryConflict(service_id=entry.service_id))
            break

        prev_end = entry.end
        prev_service_id = entry.service_id
        prev_ends_at_yard = entry.ends_at_yard

    return (low_battery, insufficient_charge)

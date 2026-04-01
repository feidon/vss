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
    service_id: int

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


@dataclass(frozen=True)
class _ServiceNode:
    service_id: int
    first_node_id: UUID
    last_node_id: UUID
    start: EpochSeconds


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
class _BatteryCost:
    cost: int
    node_type: NodeType
    service_id: int


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

    windows, nodes = _build_service_windows(candidate.vehicle_id, all_services)
    block_occupancies, group_occupancies = _build_occupancies(all_services, blocks)

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

    vehicle_conflicts = (
        _detect_time_overlap_conflicts(candidate.vehicle_id, windows)
        + _detect_location_discontinuity_conflicts(candidate.vehicle_id, nodes)
    )

    return ServiceConflicts(
        vehicle_conflicts=vehicle_conflicts,
        block_conflicts=_detect_block_conflicts(block_occupancies),
        interlocking_conflicts=_detect_interlocking_conflicts(group_occupancies),
        low_battery_conflicts=low_battery,
        insufficient_charge_conflicts=insufficient_charge,
    )


# ── Data preparation ───────────────────────────────────────


def _build_service_windows(
    vehicle_id: UUID,
    services: list[Service],
) -> tuple[list[_ServiceWindow], list[_ServiceNode]]:
    windows: list[_ServiceWindow] = []
    nodes: list[_ServiceNode] = []
    for svc in services:
        if svc.vehicle_id != vehicle_id or not svc.timetable:
            continue
        
        entries = sorted(svc.timetable, key=lambda e: e.order)
        
        windows.append(_ServiceWindow(
            service_id=svc.id,
            start=min(e.arrival for e in entries),
            end=max(e.departure for e in entries),
        ))
        
        nodes.append(_ServiceNode(
            service_id=svc.id,
            first_node_id=entries[0].node_id,
            last_node_id=entries[-1].node_id,
            start=min(e.arrival for e in entries),
        ))
        
    windows.sort(key=lambda w: w.start)
    nodes.sort(key=lambda w: w.start)
    return (windows, nodes)


def _build_occupancies(
    services: list[Service],
    blocks: list[Block],
) -> tuple[dict[UUID, list[_BlockOccupancy]], dict[int, list[_GroupOccupancy]]]:
    block_by_id = {b.id: b for b in blocks}
    by_block: dict[UUID, list[_BlockOccupancy]] = defaultdict(list)
    by_group: dict[int, list[_GroupOccupancy]] = defaultdict(list)
    for svc in services:
        for entry in svc.timetable:
            block = block_by_id.get(entry.node_id)
            if block is None:
                continue
            by_block[entry.node_id].append(
                _BlockOccupancy(svc.id, entry.arrival, entry.departure),
            )
            by_group[block.group].append(
                _GroupOccupancy(svc.id, block.id, entry.arrival, entry.departure),
            )
    return (by_block, by_group)


def _build_battery_entries(
    vehicle_id: UUID,
    services: list[Service],
) -> list[_BatteryCost]:
    entries: list[tuple[EpochSeconds, NodeType, int]] = []

    for service in services:
        if service.vehicle_id != vehicle_id:
            continue

        if not service.timetable:
            continue

        node_map = {n.id:n.type for n in service.path}
        for t in service.timetable:
            if node_map[t.node_id] != NodeType.PLATFORM:
                entries.append((t.arrival, node_map[t.node_id], service.id))

    entries.sort(key=lambda e: e[0])

    costs: list[_BatteryCost] = []
    for i in range(len(entries)):
        if entries[i][1] == NodeType.YARD:
            if i + 1 < len(entries):
                charge_time = entries[i + 1][0] - entries[i][0]
            else:
                charge_time = 0
            costs.append(_BatteryCost(charge_time, NodeType.YARD, entries[i][2]))
        else:
            costs.append(_BatteryCost(1, NodeType.BLOCK, entries[i][2]))

    return costs


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


def _detect_time_overlap_conflicts(
    vehicle_id: UUID,
    windows: list[_ServiceWindow],
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


def _detect_location_discontinuity_conflicts(
    vehicle_id: UUID,
    nodes: list[_ServiceNode],
) -> list[VehicleConflict]:
    conflicts: list[VehicleConflict] = []
    for i in range(1, len(nodes)):
        prev, curr = nodes[i - 1], nodes[i]
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
    entries: list[_BatteryCost],
) -> tuple[list[LowBatteryConflict], list[InsufficientChargeConflict]]:
    low_battery: list[LowBatteryConflict] = []
    insufficient_charge: list[InsufficientChargeConflict] = []

    if not entries:
        return (low_battery, insufficient_charge)

    sim = Vehicle(id=UUID(int=0), name="", battery=initial_battery)

    for entry in entries:
        if entry.node_type == NodeType.YARD:
            sim.charge(entry.cost)
            if not sim.can_depart():
                insufficient_charge.append(InsufficientChargeConflict(service_id=entry.service_id))
                break
        else:
            sim.consume_battery(entry.cost)
            if sim.is_battery_critical():
                low_battery.append(LowBatteryConflict(service_id=entry.service_id))
                break

    return (low_battery, insufficient_charge)

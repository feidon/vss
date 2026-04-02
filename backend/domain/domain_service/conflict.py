from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field, replace
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

    @classmethod
    def from_overlap(cls, block_id: UUID, a: _BlockOccupancy, b: _BlockOccupancy) -> BlockConflict:
        return cls(
            block_id=block_id,
            service_a_id=a.service_id,
            service_b_id=b.service_id,
            overlap_start=b.arrival,
            overlap_end=a.departure,
        )


@dataclass(frozen=True)
class InterlockingConflict:
    group: int
    block_a_id: UUID
    block_b_id: UUID
    service_a_id: int
    service_b_id: int
    overlap_start: int
    overlap_end: int

    @classmethod
    def from_overlap(cls, group: int, a: _GroupOccupancy, b: _GroupOccupancy) -> InterlockingConflict:
        return cls(
            group=group,
            block_a_id=a.block_id,
            block_b_id=b.block_id,
            service_a_id=a.service_id,
            service_b_id=b.service_id,
            overlap_start=b.arrival,
            overlap_end=a.departure,
        )

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
class _ServiceEndpoints:
    service_id: int
    first_node_id: UUID
    last_node_id: UUID
    start: EpochSeconds


@dataclass(frozen=True)
class _VehicleSchedule:
    windows: list[_ServiceWindow]
    endpoints: list[_ServiceEndpoints]


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
class _NodeEntry:
    """Intermediate timetable entry for battery simulation."""
    time: EpochSeconds
    node_type: NodeType
    service_id: int


@dataclass(frozen=True)
class _ChargeStop:
    """A yard stop where the vehicle charges."""
    charge_seconds: int
    service_id: int


@dataclass(frozen=True)
class _BlockTraversal:
    """A block traversal that consumes 1% battery."""
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

    schedule = _build_vehicle_schedule(candidate.vehicle_id, all_services)
    block_occupancies, group_occupancies = _build_occupancies(all_services, blocks)

    low_battery: list[LowBatteryConflict] = []
    insufficient_charge: list[InsufficientChargeConflict] = []
    if vehicles:
        vehicle_by_id = {v.id: v for v in vehicles}
        candidate_vehicle = vehicle_by_id.get(candidate.vehicle_id)
        if candidate_vehicle is not None:
            battery_steps = _build_battery_steps(
                candidate_vehicle.id, all_services,
            )
            low_battery, insufficient_charge = _detect_battery_conflicts(
                candidate_vehicle, battery_steps,
            )

    vehicle_conflicts = (
        _detect_time_overlap_conflicts(candidate.vehicle_id, schedule.windows)
        + _detect_location_discontinuity_conflicts(candidate.vehicle_id, schedule.endpoints)
    )

    return ServiceConflicts(
        vehicle_conflicts=vehicle_conflicts,
        block_conflicts=_detect_block_conflicts(block_occupancies),
        interlocking_conflicts=_detect_interlocking_conflicts(group_occupancies),
        low_battery_conflicts=low_battery,
        insufficient_charge_conflicts=insufficient_charge,
    )


# ── Data preparation ───────────────────────────────────────


def _build_vehicle_schedule(
    vehicle_id: UUID,
    services: list[Service],
) -> _VehicleSchedule:
    windows: list[_ServiceWindow] = []
    endpoints: list[_ServiceEndpoints] = []
    for svc in services:
        if svc.vehicle_id != vehicle_id or not svc.timetable:
            continue

        entries = sorted(svc.timetable, key=lambda e: e.order)

        windows.append(_ServiceWindow(
            service_id=svc.id,
            start=min(e.arrival for e in entries),
            end=max(e.departure for e in entries),
        ))

        endpoints.append(_ServiceEndpoints(
            service_id=svc.id,
            first_node_id=entries[0].node_id,
            last_node_id=entries[-1].node_id,
            start=min(e.arrival for e in entries),
        ))

    windows.sort(key=lambda w: w.start)
    endpoints.sort(key=lambda w: w.start)
    return _VehicleSchedule(windows, endpoints)


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


def _build_battery_steps(
    vehicle_id: UUID,
    services: list[Service],
) -> list[_ChargeStop | _BlockTraversal]:
    node_entries: list[_NodeEntry] = []

    for service in services:
        if service.vehicle_id != vehicle_id or not service.timetable:
            continue

        node_map = {n.id: n.type for n in service.path}
        for t in service.timetable:
            if node_map[t.node_id] != NodeType.PLATFORM:
                node_entries.append(_NodeEntry(t.arrival, node_map[t.node_id], service.id))

    node_entries.sort(key=lambda e: e.time)

    steps: list[_ChargeStop | _BlockTraversal] = []
    for i, entry in enumerate(node_entries):
        if entry.node_type == NodeType.YARD:
            next_time = node_entries[i + 1].time if i + 1 < len(node_entries) else entry.time
            steps.append(_ChargeStop(next_time - entry.time, entry.service_id))
        else:
            steps.append(_BlockTraversal(entry.service_id))

    return steps


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
    endpoints: list[_ServiceEndpoints],
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


def _detect_block_conflicts(
    by_block: dict[UUID, list[_BlockOccupancy]],
) -> list[BlockConflict]:
    conflicts: list[BlockConflict] = []
    for block_id, occupancies in by_block.items():
        for a, b in _find_time_overlaps(occupancies):
            conflicts.append(BlockConflict.from_overlap(block_id, a, b))
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
            conflicts.append(InterlockingConflict.from_overlap(group, a, b))
    return conflicts


def _detect_battery_conflicts(
    vehicle: Vehicle,
    steps: list[_ChargeStop | _BlockTraversal],
) -> tuple[list[LowBatteryConflict], list[InsufficientChargeConflict]]:
    low_battery: list[LowBatteryConflict] = []
    insufficient_charge: list[InsufficientChargeConflict] = []

    if not steps:
        return (low_battery, insufficient_charge)

    sim = replace(vehicle)

    for step in steps:
        match step:
            case _ChargeStop():
                sim.charge(step.charge_seconds)
                if not sim.can_depart():
                    insufficient_charge.append(InsufficientChargeConflict(service_id=step.service_id))
                    break
            case _BlockTraversal():
                sim.traverse_block()
                if sim.is_battery_critical():
                    low_battery.append(LowBatteryConflict(service_id=step.service_id))
                    break

    return (low_battery, insufficient_charge)

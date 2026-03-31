from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from uuid import UUID

from domain.block.model import Block
from domain.service.model import Service, TimetableEntry


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
class ServiceConflicts:
    vehicle_conflicts: list[VehicleConflict]
    block_conflicts: list[BlockConflict]
    interlocking_conflicts: list[InterlockingConflict]

    @property
    def has_conflicts(self) -> bool:
        return bool(self.vehicle_conflicts or self.block_conflicts or self.interlocking_conflicts)


# ── Domain Service (pure — no repository dependencies) ────


class ConflictDetectionService:
    @staticmethod
    def validate_service(
        candidate: Service, other_services: list[Service], blocks: list[Block]
    ) -> ServiceConflicts:
        """Check all conflicts for a candidate service against other services."""
        all_services = [s for s in other_services if s.id != candidate.id]
        all_services.append(candidate)
        vehicle_conflicts = _detect_vehicle_conflicts(candidate.vehicle_id, all_services)
        block_conflicts = _detect_block_conflicts(all_services, blocks)
        interlocking_conflicts = _detect_interlocking_conflicts(all_services, blocks)

        return ServiceConflicts(
            vehicle_conflicts=vehicle_conflicts,
            block_conflicts=block_conflicts,
            interlocking_conflicts=interlocking_conflicts,
        )



# ── Pure functions ───────────────────────────────────────────


def _detect_vehicle_conflicts(
    vehicle_id: UUID, all_services: list[Service]
) -> list[VehicleConflict]:
    vehicle_services = [s for s in all_services if s.vehicle_id == vehicle_id]

    windows: list[tuple[int, int, int, UUID, UUID]] = []
    for service in vehicle_services:
        if not service.timetable:
            continue
        entries = sorted(service.timetable, key=lambda e: e.order)
        min_arrival = min(e.arrival for e in entries)
        max_departure = max(e.departure for e in entries)
        windows.append((service.id, min_arrival, max_departure, entries[0].node_id, entries[-1].node_id))

    windows.sort(key=lambda w: w[1])

    conflicts: list[VehicleConflict] = []

    # Overlap detection: all pairs
    for i in range(len(windows)):
        for j in range(i + 1, len(windows)):
            prev, curr = windows[i], windows[j]
            if curr[1] >= prev[2]:
                break
            conflicts.append(VehicleConflict(vehicle_id, prev[0], curr[0], "Overlapping time windows"))

    # Location discontinuity: consecutive pairs only
    for i in range(1, len(windows)):
        prev, curr = windows[i - 1], windows[i]
        if curr[3] != prev[4]:
            conflicts.append(VehicleConflict(vehicle_id, prev[0], curr[0], "Location discontinuity"))

    return conflicts


def _detect_block_conflicts(
    services: list[Service], blocks: list[Block]
) -> list[BlockConflict]:
    block_ids = {b.id for b in blocks}

    by_block: dict[UUID, list[tuple[int, TimetableEntry]]] = defaultdict(list)
    for service in services:
        for entry in service.timetable:
            if entry.node_id in block_ids:
                by_block[entry.node_id].append((service.id, entry))

    conflicts: list[BlockConflict] = []
    for block_id, block_entries in by_block.items():
        sorted_entries = sorted(block_entries, key=lambda x: x[1].arrival)
        for i in range(len(sorted_entries)):
            sid_i, entry_i = sorted_entries[i]
            for j in range(i + 1, len(sorted_entries)):
                sid_j, entry_j = sorted_entries[j]
                if entry_j.arrival >= entry_i.departure:
                    break
                conflicts.append(BlockConflict(
                    block_id=block_id,
                    service_a_id=sid_i,
                    service_b_id=sid_j,
                    overlap_start=entry_j.arrival,
                    overlap_end=entry_i.departure,
                ))

    return conflicts


def _detect_interlocking_conflicts(
    services: list[Service], blocks: list[Block]
) -> list[InterlockingConflict]:
    """Check if two different blocks in the same interlocking group
    are occupied by different services at overlapping times."""
    block_by_id = {b.id: b for b in blocks}

    # Group timetable entries by interlocking group
    by_group: dict[int, list[tuple[int, UUID, TimetableEntry]]] = defaultdict(list)
    for service in services:
        for entry in service.timetable:
            block = block_by_id.get(entry.node_id)
            if block is not None:
                by_group[block.group].append((service.id, block.id, entry))

    conflicts: list[InterlockingConflict] = []
    for group, entries in by_group.items():
        sorted_entries = sorted(entries, key=lambda x: x[2].arrival)
        for i in range(len(sorted_entries)):
            sid_i, bid_i, entry_i = sorted_entries[i]
            for j in range(i + 1, len(sorted_entries)):
                sid_j, bid_j, entry_j = sorted_entries[j]
                if entry_j.arrival >= entry_i.departure:
                    break
                # Same block overlap is already caught by block conflict detection
                if bid_i == bid_j:
                    continue
                conflicts.append(InterlockingConflict(
                    group=group,
                    block_a_id=bid_i,
                    block_b_id=bid_j,
                    service_a_id=sid_i,
                    service_b_id=sid_j,
                    overlap_start=entry_j.arrival,
                    overlap_end=entry_i.departure,
                ))

    return conflicts

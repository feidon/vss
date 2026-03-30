from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from uuid import UUID

from domain.block.repository import BlockRepository
from domain.service.model import TimetableEntry
from domain.service.repository import ServiceRepository


# ── Value Objects ────────────────────────────────────────────


@dataclass(frozen=True)
class VehicleConflict:
    vehicle_id: UUID
    service_a_id: UUID
    service_b_id: UUID
    reason: str


@dataclass(frozen=True)
class BlockConflict:
    block_id: UUID
    service_a_id: UUID
    service_b_id: UUID
    overlap_start: int
    overlap_end: int


# ── Domain Service ───────────────────────────────────────────


class ConflictDetectionService:
    def __init__(self, service_repo: ServiceRepository, block_repo: BlockRepository) -> None:
        self._service_repo = service_repo
        self._block_repo = block_repo

    async def detect_vehicle_conflicts(self, vehicle_id: UUID) -> list[VehicleConflict]:
        """Check overlapping time windows and location discontinuity
        across services assigned to the same vehicle."""
        services = await self._service_repo.find_by_vehicle_id(vehicle_id=vehicle_id)

        windows: list[tuple[UUID, int, int, UUID, UUID]] = []
        for service in services:
            if not service.timetable:
                continue
            entries = sorted(service.timetable, key=lambda e: e.order)
            min_arrival = min(e.arrival for e in entries)
            max_departure = max(e.departure for e in entries)
            windows.append((service.id, min_arrival, max_departure, entries[0].node_id, entries[-1].node_id))

        windows.sort(key=lambda w: w[1])

        conflicts: list[VehicleConflict] = []
        for i in range(1, len(windows)):
            prev, curr = windows[i - 1], windows[i]
            if curr[1] < prev[2]:
                conflicts.append(VehicleConflict(vehicle_id, prev[0], curr[0], "Overlapping time windows"))
            elif curr[3] != prev[4]:
                conflicts.append(VehicleConflict(vehicle_id, prev[0], curr[0], "Location discontinuity"))

        return conflicts

    async def detect_block_conflicts(self) -> list[BlockConflict]:
        """Check if multiple vehicles occupy the same block
        during overlapping time windows."""
        services = await self._service_repo.find_all()
        blocks = await self._block_repo.find_all()
        block_ids = {b.id for b in blocks}

        by_block: dict[UUID, list[tuple[UUID, TimetableEntry]]] = defaultdict(list)
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

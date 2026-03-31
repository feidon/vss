from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from uuid import UUID

from domain.network.model import NodeType
from domain.shared.types import EpochSeconds
from domain.vehicle.model import Vehicle
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


# ── Domain Service (pure — no repository dependencies) ────


class ConflictDetector:

    @classmethod
    def validate_service(
        cls,
        candidate: Service,
        other_services: list[Service],
        blocks: list[Block],
        vehicles: list[Vehicle] | None = None,
    ) -> ServiceConflicts:
        """Check all conflicts for a candidate service against other services."""
        all_services = [s for s in other_services if s.id != candidate.id]
        all_services.append(candidate)

        low_battery: list[LowBatteryConflict] = []
        insufficient_charge: list[InsufficientChargeConflict] = []
        if vehicles:
            vehicle_by_id = {v.id: v for v in vehicles}
            candidate_vehicle = vehicle_by_id.get(candidate.vehicle_id)
            if candidate_vehicle is not None:
                low_battery, insufficient_charge = cls._detect_battery_conflict(
                    candidate_vehicle, all_services,
                )

        return ServiceConflicts(
            vehicle_conflicts=cls._detect_vehicle_conflicts(
                candidate.vehicle_id, all_services,
            ),
            block_conflicts=cls._detect_block_conflicts(all_services, blocks),
            interlocking_conflicts=cls._detect_interlocking_conflicts(
                all_services, blocks,
            ),
            low_battery_conflicts=low_battery,
            insufficient_charge_conflicts=insufficient_charge,
        )

    # ── Private helpers ──────────────────────────────────────

    @staticmethod
    def _find_time_overlaps[T](
        entries: list[T],
        time_of: Callable[[T], TimetableEntry],
    ) -> list[tuple[T, T]]:
        """Find all pairs with overlapping time windows.

        Sweep-line algorithm: sort by arrival, break inner loop
        when next arrival >= current departure.
        """
        sorted_entries = sorted(entries, key=lambda x: time_of(x).arrival)
        pairs: list[tuple[T, T]] = []

        for i in range(len(sorted_entries)):
            dep_i = time_of(sorted_entries[i]).departure
            for j in range(i + 1, len(sorted_entries)):
                if time_of(sorted_entries[j]).arrival >= dep_i:
                    break
                pairs.append((sorted_entries[i], sorted_entries[j]))

        return pairs

    @staticmethod
    def _detect_vehicle_conflicts(
        vehicle_id: UUID,
        all_services: list[Service],
    ) -> list[VehicleConflict]:
        vehicle_services = [s for s in all_services if s.vehicle_id == vehicle_id]

        windows: list[tuple[int, int, int, UUID, UUID]] = []
        for svc in vehicle_services:
            if not svc.timetable:
                continue
            entries = sorted(svc.timetable, key=lambda e: e.order)
            windows.append((
                svc.id,
                min(e.arrival for e in entries),
                max(e.departure for e in entries),
                entries[0].node_id,
                entries[-1].node_id,
            ))

        windows.sort(key=lambda w: w[1])
        conflicts: list[VehicleConflict] = []

        # Overlap detection
        for i in range(len(windows)):
            for j in range(i + 1, len(windows)):
                prev, curr = windows[i], windows[j]
                if curr[1] >= prev[2]:
                    break
                conflicts.append(VehicleConflict(
                    vehicle_id, prev[0], curr[0], "Overlapping time windows",
                ))

        # Location discontinuity
        for i in range(1, len(windows)):
            prev, curr = windows[i - 1], windows[i]
            if curr[3] != prev[4]:
                conflicts.append(VehicleConflict(
                    vehicle_id, prev[0], curr[0], "Location discontinuity",
                ))

        return conflicts

    @classmethod
    def _detect_block_conflicts(
        cls,
        services: list[Service],
        blocks: list[Block],
    ) -> list[BlockConflict]:
        block_ids = {b.id for b in blocks}

        by_block: dict[UUID, list[tuple[int, TimetableEntry]]] = defaultdict(list)
        for svc in services:
            for entry in svc.timetable:
                if entry.node_id in block_ids:
                    by_block[entry.node_id].append((svc.id, entry))

        conflicts: list[BlockConflict] = []
        for block_id, entries in by_block.items():
            for (sid_a, te_a), (sid_b, te_b) in cls._find_time_overlaps(
                entries, lambda x: x[1],
            ):
                conflicts.append(BlockConflict(
                    block_id=block_id,
                    service_a_id=sid_a,
                    service_b_id=sid_b,
                    overlap_start=te_b.arrival,
                    overlap_end=te_a.departure,
                ))

        return conflicts

    @classmethod
    def _detect_interlocking_conflicts(
        cls,
        services: list[Service],
        blocks: list[Block],
    ) -> list[InterlockingConflict]:
        """Detect different blocks in the same interlocking group
        occupied by different services at overlapping times."""
        block_by_id = {b.id: b for b in blocks}

        by_group: dict[int, list[tuple[int, UUID, TimetableEntry]]] = defaultdict(list)
        for svc in services:
            for entry in svc.timetable:
                block = block_by_id.get(entry.node_id)
                if block is not None:
                    by_group[block.group].append((svc.id, block.id, entry))

        conflicts: list[InterlockingConflict] = []
        for group, entries in by_group.items():
            for (sid_a, bid_a, te_a), (sid_b, bid_b, te_b) in cls._find_time_overlaps(
                entries, lambda x: x[2],
            ):
                if bid_a == bid_b:
                    continue  # already caught by block conflict detection
                conflicts.append(InterlockingConflict(
                    group=group,
                    block_a_id=bid_a,
                    block_b_id=bid_b,
                    service_a_id=sid_a,
                    service_b_id=sid_b,
                    overlap_start=te_b.arrival,
                    overlap_end=te_a.departure,
                ))

        return conflicts
    
    @classmethod
    def _detect_battery_conflict(
        cls,
        vehicle: Vehicle,
        services: list[Service],
    ) -> tuple[list[LowBatteryConflict], list[InsufficientChargeConflict]]:
        # Operate on a copy to avoid mutating the domain entity
        sim = Vehicle(id=vehicle.id, name=vehicle.name, battery=100)

        block_count: list[tuple[int, int, EpochSeconds, EpochSeconds]] = []

        for service in services:
            if service.vehicle_id != vehicle.id:
                continue

            timetable = sorted(service.timetable, key=lambda t: t.order)
            if not timetable:
                continue

            start_time = timetable[0].arrival
            end_time = timetable[-1].departure
            block_num = len([n for n in service.path if n.type == NodeType.BLOCK])
            block_count.append((service.id, block_num, start_time, end_time))

        block_count.sort(key=lambda b: b[2])

        low_battery_conflicts: list[LowBatteryConflict] = []
        insufficient_charge_conflicts: list[InsufficientChargeConflict] = []

        if not block_count:
            return (low_battery_conflicts, insufficient_charge_conflicts)

        prev_end = block_count[0][2]
        prev_service_id = block_count[0][0]
        for service_id, num, start, end in block_count:
            sim.charge(start - prev_end)
            if not sim.can_depart():
                insufficient_charge_conflicts.append(InsufficientChargeConflict(
                    service_a_id=prev_service_id,
                    service_b_id=service_id,
                ))
                break

            sim.consume_battery(num)
            if sim.is_battery_critical():
                low_battery_conflicts.append(LowBatteryConflict(service_id=service_id))
                break

            prev_end = end
            prev_service_id = service_id

        return (low_battery_conflicts, insufficient_charge_conflicts)
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from domain.block.model import Block
from domain.service.model import Service
from domain.shared.types import EpochSeconds


class Timed(Protocol):
    arrival: EpochSeconds
    departure: EpochSeconds


@dataclass(frozen=True)
class ServiceWindow:
    service_id: int
    start: EpochSeconds
    end: EpochSeconds


@dataclass(frozen=True)
class ServiceEndpoints:
    service_id: int
    first_node_id: UUID
    last_node_id: UUID
    start: EpochSeconds


@dataclass(frozen=True)
class VehicleSchedule:
    windows: list[ServiceWindow]
    endpoints: list[ServiceEndpoints]


@dataclass(frozen=True)
class BlockOccupancy:
    service_id: int
    arrival: EpochSeconds
    departure: EpochSeconds


@dataclass(frozen=True)
class GroupOccupancy:
    service_id: int
    block_id: UUID
    arrival: EpochSeconds
    departure: EpochSeconds


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


def build_vehicle_schedule(
    vehicle_id: UUID,
    services: list[Service],
) -> VehicleSchedule:
    windows: list[ServiceWindow] = []
    endpoints: list[ServiceEndpoints] = []
    for svc in services:
        if svc.vehicle_id != vehicle_id or not svc.timetable:
            continue

        entries = sorted(svc.timetable, key=lambda e: e.order)

        windows.append(
            ServiceWindow(
                service_id=svc.id,
                start=min(e.arrival for e in entries),
                end=max(e.departure for e in entries),
            )
        )

        endpoints.append(
            ServiceEndpoints(
                service_id=svc.id,
                first_node_id=entries[0].node_id,
                last_node_id=entries[-1].node_id,
                start=min(e.arrival for e in entries),
            )
        )

    windows.sort(key=lambda w: w.start)
    endpoints.sort(key=lambda w: w.start)
    return VehicleSchedule(windows, endpoints)


def build_occupancies(
    services: list[Service],
    blocks: list[Block],
) -> tuple[dict[UUID, list[BlockOccupancy]], dict[int, list[GroupOccupancy]]]:
    block_by_id = {b.id: b for b in blocks}
    by_block: dict[UUID, list[BlockOccupancy]] = defaultdict(list)
    by_group: dict[int, list[GroupOccupancy]] = defaultdict(list)
    for svc in services:
        for entry in svc.timetable:
            block = block_by_id.get(entry.node_id)
            if block is None:
                continue
            by_block[entry.node_id].append(
                BlockOccupancy(svc.id, entry.arrival, entry.departure),
            )
            by_group[block.group].append(
                GroupOccupancy(svc.id, block.id, entry.arrival, entry.departure),
            )
    return by_block, by_group

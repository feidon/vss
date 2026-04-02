from __future__ import annotations

from collections import defaultdict
from uuid import UUID

from domain.block.model import Block
from domain.domain_service.conflict.model import (
    BlockOccupancy,
    BlockTraversal,
    ChargeStop,
    GroupOccupancy,
    NodeEntry,
    ServiceEndpoints,
    ServiceWindow,
    VehicleSchedule,
)
from domain.network.model import NodeType
from domain.service.model import Service


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
    return (by_block, by_group)


def build_battery_steps(
    vehicle_id: UUID,
    services: list[Service],
) -> list[ChargeStop | BlockTraversal]:
    node_entries: list[NodeEntry] = []

    for service in services:
        if service.vehicle_id != vehicle_id or not service.timetable:
            continue

        node_map = {n.id: n.type for n in service.path}
        for t in service.timetable:
            if node_map[t.node_id] != NodeType.PLATFORM:
                node_entries.append(
                    NodeEntry(t.arrival, node_map[t.node_id], service.id)
                )

    node_entries.sort(key=lambda e: e.time)

    steps: list[ChargeStop | BlockTraversal] = []
    for i, entry in enumerate(node_entries):
        if entry.node_type == NodeType.YARD:
            next_time = (
                node_entries[i + 1].time if i + 1 < len(node_entries) else entry.time
            )
            steps.append(ChargeStop(next_time - entry.time, entry.service_id))
        else:
            steps.append(BlockTraversal(entry.service_id))

    return steps

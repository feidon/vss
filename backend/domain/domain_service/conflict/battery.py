from __future__ import annotations

from dataclasses import dataclass, replace
from uuid import UUID

from domain.domain_service.conflict.model import BatteryConflict, BatteryConflictType
from domain.network.model import NodeType
from domain.service.model import Service
from domain.shared.types import EpochSeconds
from domain.vehicle.model import Vehicle


@dataclass(frozen=True)
class NodeEntry:
    """Intermediate timetable entry for battery simulation."""

    time: EpochSeconds
    node_type: NodeType
    service_id: int


@dataclass(frozen=True)
class ChargeStop:
    """A yard stop where the vehicle charges."""

    charge_seconds: int
    service_id: int


@dataclass(frozen=True)
class BlockTraversal:
    """A block traversal that consumes 1% battery."""

    service_id: int


def build_battery_steps(
    vehicle_id: UUID,
    services: list[Service],
) -> list[ChargeStop | BlockTraversal]:
    node_entries: list[NodeEntry] = []

    for service in services:
        if service.vehicle_id != vehicle_id or not service.timetable:
            continue

        node_map = {n.id: n.type for n in service.route}
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


def detect_battery_conflicts(
    vehicle: Vehicle,
    steps: list[ChargeStop | BlockTraversal],
) -> list[BatteryConflict]:
    battery_conflicts: list[BatteryConflict] = []

    if not steps:
        return battery_conflicts

    sim = replace(vehicle)

    for step in steps:
        match step:
            case ChargeStop():
                sim.charge(step.charge_seconds)
                if not sim.can_depart():
                    battery_conflicts.append(
                        BatteryConflict(
                            type=BatteryConflictType.INSUFCHARGE,
                            service_id=step.service_id,
                        )
                    )
                    break
            case BlockTraversal():
                sim.traverse_block()
                if sim.is_battery_critical():
                    battery_conflicts.append(
                        BatteryConflict(
                            type=BatteryConflictType.LOWBATTERY,
                            service_id=step.service_id,
                        )
                    )
                    break

    return battery_conflicts

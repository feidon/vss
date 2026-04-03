from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol
from uuid import UUID

from domain.network.model import NodeType
from domain.shared.types import EpochSeconds

# ── Public conflict types ──────────────────────────────────


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
    def from_overlap(
        cls, block_id: UUID, a: BlockOccupancy, b: BlockOccupancy
    ) -> BlockConflict:
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
    def from_overlap(
        cls, group: int, a: GroupOccupancy, b: GroupOccupancy
    ) -> InterlockingConflict:
        return cls(
            group=group,
            block_a_id=a.block_id,
            block_b_id=b.block_id,
            service_a_id=a.service_id,
            service_b_id=b.service_id,
            overlap_start=b.arrival,
            overlap_end=a.departure,
        )


class BatteryConflictType(Enum):
    LOWBATTERY = "low_battery"
    INSUFCHARGE = "insufficient_charge"


@dataclass(frozen=True)
class BatteryConflict:
    type: BatteryConflictType
    service_id: int


@dataclass(frozen=True)
class InsufficientChargeConflict:
    service_id: int


@dataclass(frozen=True)
class ServiceConflicts:
    vehicle_conflicts: list[VehicleConflict]
    block_conflicts: list[BlockConflict]
    interlocking_conflicts: list[InterlockingConflict]
    battery_conflicts: list[BatteryConflict] = field(default_factory=list)

    @property
    def has_conflicts(self) -> bool:
        return bool(
            self.vehicle_conflicts
            or self.block_conflicts
            or self.interlocking_conflicts
            or self.battery_conflicts
        )


# ── Data structures ────────────────────────────────────────


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

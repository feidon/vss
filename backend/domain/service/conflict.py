from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import time
from uuid import UUID

from domain.service.model import Service


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
    vehicle_a_id: UUID
    vehicle_b_id: UUID
    overlap_start: time
    overlap_end: time


# ── Ports ────────────────────────────────────────────────────


class ServiceQueryPort(ABC):
    @abstractmethod
    async def find_by_vehicle_id(self, vehicle_id: UUID) -> list[Service]: ...

    @abstractmethod
    async def find_all(self) -> list[Service]: ...


class BlockQueryPort(ABC):
    @abstractmethod
    async def get_traversal_time_seconds(self, block_id: UUID) -> int: ...


# ── Domain Service ───────────────────────────────────────────


class ConflictDetectionService:
    def __init__(
        self, service_query: ServiceQueryPort, block_query: BlockQueryPort
    ) -> None:
        self._service_query = service_query
        self._block_query = block_query

    async def detect_vehicle_conflicts(
        self, vehicle_id: UUID
    ) -> list[VehicleConflict]:
        """Check overlapping time windows and location discontinuity
        across services assigned to the same vehicle."""
        raise NotImplementedError

    async def detect_block_conflicts(self) -> list[BlockConflict]:
        """Check if multiple vehicles occupy the same block
        during overlapping time windows.

        A vehicle occupies a block for the duration of its
        configured traversal_time_seconds."""
        raise NotImplementedError

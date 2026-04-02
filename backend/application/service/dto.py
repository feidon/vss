from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from domain.domain_service.conflict.model import (
    InsufficientChargeConflict,
    LowBatteryConflict,
)
from domain.network.model import Node


@dataclass(frozen=True)
class RouteStop:
    node_id: UUID
    dwell_time: int  # seconds


@dataclass(frozen=True)
class RouteValidationResult:
    route: list[Node]
    battery_conflicts: list[LowBatteryConflict | InsufficientChargeConflict]

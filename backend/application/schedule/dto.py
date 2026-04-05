from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from domain.shared.types import EpochSeconds


@dataclass(frozen=True)
class GenerateScheduleRequest:
    interval_seconds: int
    start_time: EpochSeconds
    end_time: EpochSeconds
    dwell_time_seconds: int


@dataclass(frozen=True)
class GenerateScheduleResponse:
    services_created: int
    vehicles_used: list[UUID]
    cycle_time_seconds: int

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class RouteStop:
    node_id: UUID
    dwell_time: int  # seconds

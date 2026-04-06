from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

CHARGE_SECONDS_PER_PERCENT = 12
DEPART_THRESHOLD = 80
TRAVERSAL_DRAIN = 1
CRITICAL_THRESHOLD = 30
MAX_BATTERY = 100


@dataclass(eq=False)
class Vehicle:
    id: UUID
    name: str
    battery: int = DEPART_THRESHOLD

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Vehicle) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    def charge(self, charge_seconds: int) -> None:
        gained = charge_seconds // CHARGE_SECONDS_PER_PERCENT
        self.battery = min(self.battery + gained, MAX_BATTERY)

    def can_depart(self) -> bool:
        return self.battery >= DEPART_THRESHOLD

    def traverse_block(self) -> None:
        self.battery -= TRAVERSAL_DRAIN

    def is_battery_critical(self) -> bool:
        return self.battery < CRITICAL_THRESHOLD

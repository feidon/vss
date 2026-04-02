from dataclasses import dataclass
from uuid import UUID


@dataclass(eq=False)
class Vehicle:
    id: UUID
    name: str
    battery: int = 80

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Vehicle) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    def charge(self, charge_seconds: int) -> None:
        self.battery = min(self.battery + charge_seconds // 12, 100)

    def can_depart(self) -> bool:
        return self.battery >= 80

    def traverse_block(self) -> None:
        self.battery -= 1

    def is_battery_critical(self) -> bool:
        return self.battery < 30

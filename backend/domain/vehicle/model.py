from dataclasses import dataclass
from uuid import UUID


@dataclass(eq=False)
class Vehicle:
    id: UUID
    name: str

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Vehicle) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
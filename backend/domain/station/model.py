from dataclasses import dataclass
from uuid import UUID

@dataclass
class Station:
    id: UUID
    name: str
    is_yard: bool
    platforms: list[Platform]

@dataclass
class Platform:
    id: UUID
    name: str
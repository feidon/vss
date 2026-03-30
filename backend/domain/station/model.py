from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from domain.network.model import Node, NodeType


@dataclass(frozen=True)
class Platform:
    id: UUID
    name: str

    def to_node(self) -> Node:
        return Node(id=self.id, type=NodeType.PLATFORM)


@dataclass(eq=False)
class Station:
    id: UUID
    name: str
    is_yard: bool
    platforms: list[Platform]

    def add_platform(self, platform: Platform) -> None:
        if any(p.id == platform.id for p in self.platforms):
            raise ValueError(f"Platform {platform.id} already exists")
        self.platforms.append(platform)

    def remove_platform(self, platform_id: UUID) -> None:
        original_len = len(self.platforms)
        self.platforms = [p for p in self.platforms if p.id != platform_id]
        if len(self.platforms) == original_len:
            raise ValueError(f"Platform {platform_id} not found")

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Station) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

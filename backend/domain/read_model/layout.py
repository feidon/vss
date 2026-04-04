from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class LayoutData:
    positions: dict[UUID, tuple[float, float]]
    junction_blocks: dict[tuple[UUID, UUID], UUID]


class LayoutRepository(ABC):
    @abstractmethod
    async def find_all(self) -> LayoutData:
        """Return layout positions and junction-block mappings."""

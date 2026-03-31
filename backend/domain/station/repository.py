from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from domain.station.model import Station


class StationRepository(ABC):
    @abstractmethod
    async def find_all(self) -> list[Station]: ...

    @abstractmethod
    async def find_by_id(self, id: UUID) -> Station | None: ...

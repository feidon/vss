from __future__ import annotations

from uuid import UUID

from domain.station.model import Station
from domain.station.repository import StationRepository


class InMemoryStationRepository(StationRepository):
    def __init__(self) -> None:
        self._store: dict[UUID, Station] = {}

    async def find_all(self) -> list[Station]:
        return list(self._store.values())

    async def find_by_id(self, id: UUID) -> Station | None:
        return self._store.get(id)

    def seed(self, station: Station) -> None:
        self._store[station.id] = station

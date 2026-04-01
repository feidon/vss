from __future__ import annotations

from uuid import UUID

from sqlalchemy import select

from domain.station.model import Station
from domain.station.repository import StationRepository
from sqlalchemy.ext.asyncio import AsyncSession


class PostgresStationRepository(StationRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_all(self) -> list[Station]:
        return (await self._session.scalars(select(Station))).all()

    async def find_by_id(self, id: UUID) -> Station | None:
        return await self._session.get(Station, id)

    async def save(self, station: Station) -> None:
        self._store[station.id] = station
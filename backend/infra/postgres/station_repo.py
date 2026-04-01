from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.station.model import Platform, Station
from domain.station.repository import StationRepository
from infra.postgres.tables import platforms_table, stations_table


class PostgresStationRepository(StationRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _base_query():
        return select(
            stations_table.c.id,
            stations_table.c.name,
            stations_table.c.is_yard,
            platforms_table.c.id.label("platform_id"),
            platforms_table.c.name.label("platform_name"),
        ).select_from(
            stations_table.outerjoin(
                platforms_table,
                stations_table.c.id == platforms_table.c.station_id,
            )
        )

    async def find_all(self) -> list[Station]:
        result = await self._session.execute(self._base_query())
        return self._group_rows(result.mappings().all())

    async def find_by_id(self, id: UUID) -> Station | None:
        result = await self._session.execute(
            self._base_query().where(stations_table.c.id == id)
        )
        rows = result.mappings().all()
        if not rows:
            return None
        return self._group_rows(rows)[0]

    @staticmethod
    def _group_rows(rows) -> list[Station]:
        stations_by_id: dict[UUID, Station] = {}
        for row in rows:
            station_id = row["id"]
            if station_id not in stations_by_id:
                stations_by_id[station_id] = Station(
                    id=station_id,
                    name=row["name"],
                    is_yard=row["is_yard"],
                    platforms=[],
                )
            if row["platform_id"] is not None:
                stations_by_id[station_id].platforms.append(
                    Platform(id=row["platform_id"], name=row["platform_name"])
                )
        return list(stations_by_id.values())

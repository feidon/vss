from __future__ import annotations

from uuid import UUID

from domain.vehicle.model import Vehicle
from domain.vehicle.repository import VehicleRepository
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from infra.postgres.tables import vehicles_table


class PostgresVehicleRepository(VehicleRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_all(self) -> list[Vehicle]:
        result = await self._session.execute(select(vehicles_table))
        return [self._to_entity(row) for row in result.mappings()]

    async def find_by_id(self, id: UUID) -> Vehicle | None:
        result = await self._session.execute(
            select(vehicles_table).where(vehicles_table.c.id == id)
        )
        row = result.mappings().first()
        return self._to_entity(row) if row else None

    @staticmethod
    def _to_entity(row) -> Vehicle:
        return Vehicle(
            id=row["id"],
            name=row["name"],
        )

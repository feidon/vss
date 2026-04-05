from __future__ import annotations

from uuid import UUID, uuid7

from domain.vehicle.model import Vehicle
from domain.vehicle.repository import VehicleRepository
from sqlalchemy import insert, select
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

    async def add_by_number(self, number: int) -> None:
        current_number = len(await self.find_all())
        for i in range(number):
            new_vehicle = Vehicle(id=uuid7(), name=f"V{current_number + i}")
            await self._session.execute(
                insert(vehicles_table).values(**self._to_table(new_vehicle))
            )
        await self._session.commit()

    @staticmethod
    def _to_entity(row) -> Vehicle:
        return Vehicle(
            id=row["id"],
            name=row["name"],
        )

    @staticmethod
    def _to_table(vehicle: Vehicle) -> dict:
        return {
            "id": vehicle.id,
            "name": vehicle.name,
        }

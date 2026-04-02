from __future__ import annotations

from uuid import UUID

from domain.network.model import Node, NodeType
from domain.service.model import Service, TimetableEntry
from domain.service.repository import ServiceRepository
from sqlalchemy import delete, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from infra.postgres.tables import services_table


class PostgresServiceRepository(ServiceRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_all(self) -> list[Service]:
        result = await self._session.execute(select(services_table))
        return [self._to_entity(row) for row in result.mappings()]

    async def find_by_id(self, id: int) -> Service | None:
        result = await self._session.execute(
            select(services_table).where(services_table.c.id == id)
        )
        row = result.mappings().first()
        return self._to_entity(row) if row else None

    async def find_by_vehicle_id(self, vehicle_id: UUID) -> list[Service]:
        result = await self._session.execute(
            select(services_table).where(services_table.c.vehicle_id == vehicle_id)
        )
        return [self._to_entity(row) for row in result.mappings()]

    async def save(self, service: Service) -> None:
        if service.id is None:
            result = await self._session.execute(
                insert(services_table)
                .values(**self._to_table_without_id(service))
                .returning(services_table.c.id)
            )
            service.id = result.scalar_one()
        else:
            await self._session.execute(
                update(services_table)
                .where(services_table.c.id == service.id)
                .values(**self._to_table_without_id(service))
            )
        await self._session.commit()

    async def delete(self, id: int) -> None:
        await self._session.execute(
            delete(services_table).where(services_table.c.id == id)
        )
        await self._session.commit()

    @staticmethod
    def _to_entity(row) -> Service:
        path = [Node(id=UUID(n["id"]), type=NodeType(n["type"])) for n in row["path"]]
        timetable = [
            TimetableEntry(
                order=e["order"],
                node_id=UUID(e["node_id"]),
                arrival=e["arrival"],
                departure=e["departure"],
            )
            for e in row["timetable"]
        ]
        return Service(
            id=row["id"],
            name=row["name"],
            vehicle_id=row["vehicle_id"],
            path=path,
            timetable=timetable,
        )

    @staticmethod
    def _to_table_without_id(service: Service) -> dict:
        return {
            "name": service.name,
            "vehicle_id": service.vehicle_id,
            "path": [{"id": str(n.id), "type": n.type.value} for n in service.path],
            "timetable": [
                {
                    "order": e.order,
                    "node_id": str(e.node_id),
                    "arrival": e.arrival,
                    "departure": e.departure,
                }
                for e in service.timetable
            ],
        }

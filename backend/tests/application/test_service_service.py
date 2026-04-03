from uuid import UUID, uuid7

import pytest
from application.service.service import ServiceAppService
from domain.error import DomainError
from domain.vehicle.model import Vehicle

from tests.fakes.block_repo import InMemoryBlockRepository
from tests.fakes.connection_repo import InMemoryConnectionRepository
from tests.fakes.service_repo import InMemoryServiceRepository
from tests.fakes.station_repo import InMemoryStationRepository
from tests.fakes.vehicle_repo import InMemoryVehicleRepository


def _make_app(
    service_repo=None,
    block_repo=None,
    connection_repo=None,
    vehicle_repo=None,
    station_repo=None,
):
    return ServiceAppService(
        service_repo=service_repo or InMemoryServiceRepository(),
        block_repo=block_repo or InMemoryBlockRepository(),
        connection_repo=connection_repo or InMemoryConnectionRepository(),
        vehicle_repo=vehicle_repo or InMemoryVehicleRepository(),
        station_repo=station_repo or InMemoryStationRepository(),
    )


def seed_vehicle(
    vehicle_repo: InMemoryVehicleRepository, vid: UUID | None = None
) -> Vehicle:
    vehicle = Vehicle(id=vid or uuid7(), name="V1")
    vehicle_repo._store[vehicle.id] = vehicle
    return vehicle


class TestServiceAppService:
    @pytest.fixture
    def vehicle_repo(self):
        return InMemoryVehicleRepository()

    @pytest.fixture
    def app(self, vehicle_repo):
        return _make_app(vehicle_repo=vehicle_repo)

    async def test_create_service(self, app, vehicle_repo):
        v = seed_vehicle(vehicle_repo)
        result = await app.create_service(name="Express", vehicle_id=v.id)
        assert result.name == "Express"
        assert result.vehicle_id == v.id
        assert result.route == []
        assert result.timetable == []

    async def test_create_service_rejects_empty_name(self, app, vehicle_repo):
        v = seed_vehicle(vehicle_repo)
        with pytest.raises(DomainError, match="name"):
            await app.create_service(name="", vehicle_id=v.id)

    async def test_create_service_rejects_unknown_vehicle(self, app):
        with pytest.raises(DomainError, match="Vehicle.*not found"):
            await app.create_service(name="S1", vehicle_id=uuid7())

    async def test_get_service(self, app, vehicle_repo):
        v = seed_vehicle(vehicle_repo)
        created = await app.create_service(name="S1", vehicle_id=v.id)
        result = await app.get_service(created.id)
        assert result == created

    async def test_get_service_not_found(self, app):
        with pytest.raises(DomainError, match="not found"):
            await app.get_service(999)

    async def test_list_services(self, app, vehicle_repo):
        v1 = seed_vehicle(vehicle_repo)
        v2 = seed_vehicle(vehicle_repo)
        await app.create_service(name="S1", vehicle_id=v1.id)
        await app.create_service(name="S2", vehicle_id=v2.id)
        result = await app.list_services()
        assert len(result) == 2

    async def test_delete_service(self):
        service_repo = InMemoryServiceRepository()
        vehicle_repo = InMemoryVehicleRepository()
        v = seed_vehicle(vehicle_repo)
        app = _make_app(service_repo=service_repo, vehicle_repo=vehicle_repo)
        created = await app.create_service(name="S1", vehicle_id=v.id)
        await app.delete_service(created.id)
        assert await service_repo.find_by_id(created.id) is None

    async def test_delete_service_idempotent(self, app):
        await app.delete_service(999)

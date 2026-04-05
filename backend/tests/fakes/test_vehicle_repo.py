from tests.fakes.vehicle_repo import InMemoryVehicleRepository


class TestInMemoryVehicleRepoAddByNumber:
    async def test_add_to_empty_repo(self):
        repo = InMemoryVehicleRepository()
        await repo.add_by_number(3)
        vehicles = await repo.find_all()
        assert len(vehicles) == 3
        names = sorted(v.name for v in vehicles)
        assert names == ["V0", "V1", "V2"]

    async def test_add_continues_naming_from_current_count(self):
        repo = InMemoryVehicleRepository()
        await repo.add_by_number(2)
        await repo.add_by_number(2)
        vehicles = await repo.find_all()
        assert len(vehicles) == 4
        names = sorted(v.name for v in vehicles)
        assert names == ["V0", "V1", "V2", "V3"]

    async def test_add_zero_creates_nothing(self):
        repo = InMemoryVehicleRepository()
        await repo.add_by_number(0)
        vehicles = await repo.find_all()
        assert len(vehicles) == 0

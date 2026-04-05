## 1. Bug Fix — Postgres Vehicle Repository

- [x] 1.1 Fix missing `await` on `self.find_all()` in `PostgresVehicleRepository.add_by_number()` (`infra/postgres/vehicle_repo.py:29`)

## 2. Repository Tests — InMemoryVehicleRepository

- [x] 2.1 Add test: `add_by_number` on empty repo creates vehicles named V0, V1, V2
- [x] 2.2 Add test: `add_by_number` on pre-populated repo continues naming from current count (V2, V3)
- [x] 2.3 Add test: `add_by_number(0)` creates no vehicles

## 3. Repository Tests — PostgresVehicleRepository

- [x] 3.1 Add Postgres integration test: `add_by_number` persists vehicles and they are retrievable via `find_all()` (mark `@pytest.mark.postgres`)
- [x] 3.2 Add Postgres integration test: `add_by_number` on pre-populated repo names vehicles sequentially

## 4. Application Tests — ScheduleAppService

- [x] 4.1 Add test: schedule generation with 0 pre-existing vehicles auto-generates required vehicles
- [x] 4.2 Add test: schedule generation with fewer vehicles than needed generates the deficit
- [x] 4.3 Add test: schedule generation with sufficient vehicles does not create new ones

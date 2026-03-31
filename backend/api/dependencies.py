from fastapi import Depends

from application.block.service import BlockAppService
from application.graph.service import GraphAppService
from application.service.service import ServiceAppService
from domain.block.repository import BlockRepository
from domain.network.repository import ConnectionRepository
from domain.service.repository import ServiceRepository
from domain.station.repository import StationRepository
from domain.vehicle.repository import VehicleRepository
from infra.memory.block_repo import InMemoryBlockRepository
from infra.memory.connection_repo import InMemoryConnectionRepository
from infra.memory.service_repo import InMemoryServiceRepository
from infra.memory.station_repo import InMemoryStationRepository
from infra.memory.vehicle_repo import InMemoryVehicleRepository
from infra.seed import create_blocks, create_connections, create_stations, create_vehicles

# ── Initialise repositories with seed data ──────────────────

_block_repo = InMemoryBlockRepository()
_service_repo = InMemoryServiceRepository()
_station_repo = InMemoryStationRepository()
_vehicle_repo = InMemoryVehicleRepository()

for _b in create_blocks():
    _block_repo._store[_b.id] = _b

for _s in create_stations():
    _station_repo._store[_s.id] = _s

for _v in create_vehicles():
    _vehicle_repo._store[_v.id] = _v

_connection_repo = InMemoryConnectionRepository(create_connections())


# ── Dependency providers ────────────────────────────────────


def get_block_repo() -> BlockRepository:
    return _block_repo


def get_service_repo() -> ServiceRepository:
    return _service_repo


def get_connection_repo() -> ConnectionRepository:
    return _connection_repo


def get_station_repo() -> StationRepository:
    return _station_repo


def get_vehicle_repo() -> VehicleRepository:
    return _vehicle_repo


def get_block_service(
    block_repo: BlockRepository = Depends(get_block_repo),
) -> BlockAppService:
    return BlockAppService(block_repo)


def get_service_app_service(
    service_repo: ServiceRepository = Depends(get_service_repo),
    block_repo: BlockRepository = Depends(get_block_repo),
    connection_repo: ConnectionRepository = Depends(get_connection_repo),
    vehicle_repo: VehicleRepository = Depends(get_vehicle_repo),
    station_repo: StationRepository = Depends(get_station_repo),
) -> ServiceAppService:
    return ServiceAppService(service_repo, block_repo, connection_repo, vehicle_repo, station_repo)


def get_graph_service(
    station_repo: StationRepository = Depends(get_station_repo),
    block_repo: BlockRepository = Depends(get_block_repo),
    connection_repo: ConnectionRepository = Depends(get_connection_repo),
    vehicle_repo: VehicleRepository = Depends(get_vehicle_repo),
) -> GraphAppService:
    return GraphAppService(station_repo, block_repo, connection_repo, vehicle_repo)

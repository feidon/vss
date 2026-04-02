from application.block.service import BlockAppService
from application.graph.service import GraphAppService
from application.service.service import ServiceAppService
from domain.block.repository import BlockRepository
from domain.network.node_layout_repository import NodeLayoutRepository
from domain.network.repository import ConnectionRepository
from domain.service.repository import ServiceRepository
from domain.station.repository import StationRepository
from domain.vehicle.repository import VehicleRepository
from fastapi import Depends
from infra.postgres.block_repo import PostgresBlockRepository
from infra.postgres.connection_repo import PostgresConnectionRepository
from infra.postgres.node_layout_repo import PostgresNodeLayoutRepository
from infra.postgres.service_repo import PostgresServiceRepository
from infra.postgres.session import get_session
from infra.postgres.station_repo import PostgresStationRepository
from infra.postgres.vehicle_repo import PostgresVehicleRepository
from sqlalchemy.ext.asyncio import AsyncSession

# ── Dependency providers ────────────────────────────────────


def get_block_repo(session: AsyncSession = Depends(get_session)):
    return PostgresBlockRepository(session)


def get_service_repo(session: AsyncSession = Depends(get_session)) -> ServiceRepository:
    return PostgresServiceRepository(session)


def get_connection_repo(
    session: AsyncSession = Depends(get_session),
) -> ConnectionRepository:
    return PostgresConnectionRepository(session)


def get_station_repo(session: AsyncSession = Depends(get_session)) -> StationRepository:
    return PostgresStationRepository(session)


def get_vehicle_repo(session: AsyncSession = Depends(get_session)) -> VehicleRepository:
    return PostgresVehicleRepository(session)


def get_node_layout_repo(
    session: AsyncSession = Depends(get_session),
) -> NodeLayoutRepository:
    return PostgresNodeLayoutRepository(session)


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
    return ServiceAppService(
        service_repo, block_repo, connection_repo, vehicle_repo, station_repo
    )


def get_graph_service(
    station_repo: StationRepository = Depends(get_station_repo),
    block_repo: BlockRepository = Depends(get_block_repo),
    connection_repo: ConnectionRepository = Depends(get_connection_repo),
    vehicle_repo: VehicleRepository = Depends(get_vehicle_repo),
    node_layout_repo: NodeLayoutRepository = Depends(get_node_layout_repo),
) -> GraphAppService:
    return GraphAppService(
        station_repo, block_repo, connection_repo, vehicle_repo, node_layout_repo
    )

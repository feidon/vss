from fastapi import Depends

from application.block.service import BlockAppService
from application.service.service import ServiceAppService
from domain.block.repository import BlockRepository
from domain.network.repository import ConnectionRepository
from domain.service.repository import ServiceRepository
from infra.memory.block_repo import InMemoryBlockRepository
from infra.memory.connection_repo import InMemoryConnectionRepository
from infra.memory.service_repo import InMemoryServiceRepository

_block_repo = InMemoryBlockRepository()
_service_repo = InMemoryServiceRepository()
_connection_repo = InMemoryConnectionRepository()


def get_block_repo() -> BlockRepository:
    return _block_repo


def get_service_repo() -> ServiceRepository:
    return _service_repo


def get_connection_repo() -> ConnectionRepository:
    return _connection_repo


def get_block_service(
    block_repo: BlockRepository = Depends(get_block_repo),
) -> BlockAppService:
    return BlockAppService(block_repo)


def get_service_app_service(
    service_repo: ServiceRepository = Depends(get_service_repo),
    block_repo: BlockRepository = Depends(get_block_repo),
    connection_repo: ConnectionRepository = Depends(get_connection_repo),
) -> ServiceAppService:
    return ServiceAppService(service_repo, block_repo, connection_repo)

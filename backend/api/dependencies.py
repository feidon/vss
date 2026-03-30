from fastapi import Depends

from application.block.service import BlockApplicationService
from application.service.service import ServiceApplicationService
from domain.block.repository import BlockRepository
from domain.service.repository import ServiceRepository
from infra.memory.block_repo import InMemoryBlockRepository
from infra.memory.service_repo import InMemoryServiceRepository

_block_repo = InMemoryBlockRepository()
_service_repo = InMemoryServiceRepository()


def get_block_repo() -> BlockRepository:
    return _block_repo


def get_service_repo() -> ServiceRepository:
    return _service_repo


def get_block_service(
    block_repo: BlockRepository = Depends(get_block_repo),
) -> BlockApplicationService:
    return BlockApplicationService(block_repo)


def get_service_service(
    service_repo: ServiceRepository = Depends(get_service_repo),
) -> ServiceApplicationService:
    return ServiceApplicationService(service_repo)

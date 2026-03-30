from fastapi import FastAPI

from api.block.routes import create_block_router
from api.service.routes import create_service_router
from application.block.service import BlockApplicationService
from application.service.service import ServiceApplicationService
from domain.block.repository import BlockRepository
from domain.service.repository import ServiceRepository
from infra.memory.block_repo import InMemoryBlockRepository
from infra.memory.service_repo import InMemoryServiceRepository


def create_app(
    block_repo: BlockRepository | None = None,
    service_repo: ServiceRepository | None = None,
) -> FastAPI:
    app = FastAPI()

    if block_repo is None:
        block_repo = InMemoryBlockRepository()
    if service_repo is None:
        service_repo = InMemoryServiceRepository()

    block_service = BlockApplicationService(block_repo)
    app.include_router(create_block_router(block_service))

    service_service = ServiceApplicationService(service_repo)
    app.include_router(create_service_router(service_service))

    return app


app = create_app()

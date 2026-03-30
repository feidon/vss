from fastapi import FastAPI

from api.block.routes import create_block_router
from application.block.service import BlockApplicationService
from domain.block.repository import BlockRepository, InMemoryBlockRepositoryImpl


def create_app(block_repo: BlockRepository | None = None) -> FastAPI:
    app = FastAPI()

    if block_repo is None:
        block_repo = InMemoryBlockRepositoryImpl()

    block_service = BlockApplicationService(block_repo)
    app.include_router(create_block_router(block_service))

    return app


app = create_app()
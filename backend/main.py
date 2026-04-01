import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.block.routes import router as block_router
from api.graph.routes import router as graph_router
from api.service.routes import router as service_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    if os.getenv("DB") == "postgres":
        from infra.postgres.seed import seed_database
        from infra.postgres.session import async_session

        async with async_session() as session:
            await seed_database(session)
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(block_router)
app.include_router(service_router)
app.include_router(graph_router)

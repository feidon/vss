import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from api.block.routes import router as block_router
from api.graph.routes import router as graph_router
from api.service.routes import router as service_router

STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    if os.getenv("DB") == "postgres":
        from infra.postgres.tables import metadata
        from infra.postgres.seed import seed_database
        from infra.postgres.session import async_session, engine

        async with engine.begin() as conn:
            await conn.run_sync(metadata.create_all)

        async with async_session() as session:
            await seed_database(session)
    yield


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(block_router)
app.include_router(service_router)
app.include_router(graph_router)

if STATIC_DIR.is_dir():

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        file_path = (STATIC_DIR / full_path).resolve()
        if file_path.is_file() and file_path.is_relative_to(STATIC_DIR.resolve()):
            return FileResponse(file_path)
        return FileResponse(STATIC_DIR / "index.html")

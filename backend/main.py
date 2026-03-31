from fastapi import FastAPI

from api.block.routes import router as block_router
from api.graph.routes import router as graph_router
from api.service.routes import router as service_router

app = FastAPI()
app.include_router(block_router)
app.include_router(service_router)
app.include_router(graph_router)

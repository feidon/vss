from contextlib import asynccontextmanager

from api.block.routes import router as block_router
from api.error_handler import domain_error_handler
from api.route.routes import router as route_router
from api.schedule.routes import router as schedule_router
from api.service.routes import router as service_router
from api.vehicle.routes import router as vehicle_router
from domain.error import DomainError
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(lifespan=lifespan)
app.add_exception_handler(DomainError, domain_error_handler)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
API_PREFIX = "/api"
app.include_router(block_router, prefix=API_PREFIX)
app.include_router(schedule_router, prefix=API_PREFIX)
app.include_router(service_router, prefix=API_PREFIX)
app.include_router(route_router, prefix=API_PREFIX)
app.include_router(vehicle_router, prefix=API_PREFIX)

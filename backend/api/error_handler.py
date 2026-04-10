from __future__ import annotations

import logging

from application.service.errors import ConflictError
from domain.error import DomainError, ErrorCode
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_409_CONFLICT,
    HTTP_422_UNPROCESSABLE_CONTENT,
)

logger = logging.getLogger(__name__)

STATUS_MAP: dict[ErrorCode, int] = {
    # 404
    ErrorCode.SERVICE_NOT_FOUND: HTTP_404_NOT_FOUND,
    ErrorCode.BLOCK_NOT_FOUND: HTTP_404_NOT_FOUND,
    # 422
    ErrorCode.NO_ROUTE_BETWEEN_STOPS: HTTP_422_UNPROCESSABLE_CONTENT,
    # 409
    ErrorCode.SCHEDULING_CONFLICT: HTTP_409_CONFLICT,
    ErrorCode.SCHEDULE_INFEASIBLE: HTTP_409_CONFLICT,
}


async def domain_error_handler(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, DomainError)
    status = STATUS_MAP.get(exc.code, HTTP_400_BAD_REQUEST)

    if isinstance(exc, ConflictError):
        context = _build_conflict_context(exc)
    else:
        context = exc.context or {}

    logger.warning(
        "Domain error: %s",
        exc.message,
        extra={"error_code": exc.code.value, "context": context},
    )

    detail = {
        "error_code": exc.code.value,
        "context": context,
    }
    return JSONResponse(status_code=status, content={"detail": detail})


def _build_conflict_context(e: ConflictError) -> dict:
    c = e.conflicts
    return {
        "vehicle_conflicts": [
            {
                "vehicle_id": str(vc.vehicle_id),
                "service_a_id": vc.service_a_id,
                "service_b_id": vc.service_b_id,
                "reason": vc.reason,
            }
            for vc in c.vehicle_conflicts
        ],
        "block_conflicts": [
            {
                "block_id": str(bc.block_id),
                "service_a_id": bc.service_a_id,
                "service_b_id": bc.service_b_id,
                "overlap_start": bc.overlap_start,
                "overlap_end": bc.overlap_end,
            }
            for bc in c.block_conflicts
        ],
        "interlocking_conflicts": [
            {
                "group": ic.group,
                "block_a_id": str(ic.block_a_id),
                "block_b_id": str(ic.block_b_id),
                "service_a_id": ic.service_a_id,
                "service_b_id": ic.service_b_id,
                "overlap_start": ic.overlap_start,
                "overlap_end": ic.overlap_end,
            }
            for ic in c.interlocking_conflicts
        ],
        "battery_conflicts": [
            {"type": lbc.type.value, "service_id": lbc.service_id}
            for lbc in c.battery_conflicts
        ],
    }

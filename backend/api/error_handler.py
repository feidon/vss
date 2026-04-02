from __future__ import annotations

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

STATUS_MAP = {
    ErrorCode.NOT_FOUND: HTTP_404_NOT_FOUND,
    ErrorCode.VALIDATION: HTTP_400_BAD_REQUEST,
    ErrorCode.CONFLICT: HTTP_409_CONFLICT,
    ErrorCode.NO_ROUTE: HTTP_422_UNPROCESSABLE_CONTENT,
}


async def domain_error_handler(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, DomainError)
    status = STATUS_MAP.get(exc.code, HTTP_400_BAD_REQUEST)
    if isinstance(exc, ConflictError):
        detail = _build_conflict_detail(exc)
    else:
        detail = exc.message
    return JSONResponse(status_code=status, content={"detail": detail})


def _build_conflict_detail(e: ConflictError) -> dict:
    c = e.conflicts
    return {
        "message": e.message,
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
        "low_battery_conflicts": [
            {"service_id": lbc.service_id} for lbc in c.low_battery_conflicts
        ],
        "insufficient_charge_conflicts": [
            {"service_id": icc.service_id} for icc in c.insufficient_charge_conflicts
        ],
    }

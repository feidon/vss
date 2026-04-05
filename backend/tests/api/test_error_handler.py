from __future__ import annotations

import json
from uuid import UUID

from api.error_handler import domain_error_handler
from api.shared.schemas import ConflictDetailResponse, ErrorResponse
from application.service.errors import ConflictError
from domain.domain_service.conflict.model import (
    BatteryConflict,
    BatteryConflictType,
    BlockConflict,
    InterlockingConflict,
    ServiceConflicts,
    VehicleConflict,
)
from domain.error import DomainError, ErrorCode


async def test_not_found_returns_404_with_structured_detail():
    exc = DomainError(
        ErrorCode.SERVICE_NOT_FOUND,
        "Service 1 not found",
        {"service_id": 1},
    )
    resp = await domain_error_handler(None, exc)

    assert resp.status_code == 404
    body = json.loads(resp.body)
    assert body["detail"]["error_code"] == "SERVICE_NOT_FOUND"
    assert body["detail"]["message"] == "Service 1 not found"
    assert body["detail"]["context"] == {"service_id": 1}


async def test_validation_returns_400_with_structured_detail():
    exc = DomainError(
        ErrorCode.STOP_NOT_FOUND,
        "Stop abc not found",
        {"stop_id": "abc"},
    )
    resp = await domain_error_handler(None, exc)

    assert resp.status_code == 400
    body = json.loads(resp.body)
    assert body["detail"]["error_code"] == "STOP_NOT_FOUND"
    assert body["detail"]["message"] == "Stop abc not found"
    assert body["detail"]["context"] == {"stop_id": "abc"}


async def test_validation_without_context_returns_empty_context():
    exc = DomainError(ErrorCode.EMPTY_SERVICE_NAME, "Service name must not be empty")
    resp = await domain_error_handler(None, exc)

    assert resp.status_code == 400
    body = json.loads(resp.body)
    assert body["detail"]["error_code"] == "EMPTY_SERVICE_NAME"
    assert body["detail"]["context"] == {}


async def test_no_route_returns_422_with_structured_detail():
    exc = DomainError(
        ErrorCode.NO_ROUTE_BETWEEN_STOPS,
        "No route between stops",
        {"from_stop_id": "abc", "to_stop_id": "def"},
    )
    resp = await domain_error_handler(None, exc)

    assert resp.status_code == 422
    body = json.loads(resp.body)
    assert body["detail"]["error_code"] == "NO_ROUTE_BETWEEN_STOPS"
    assert body["detail"]["context"]["from_stop_id"] == "abc"
    assert body["detail"]["context"]["to_stop_id"] == "def"


async def test_conflict_error_returns_409_with_structured_detail():
    conflicts = ServiceConflicts(
        vehicle_conflicts=[
            VehicleConflict(
                vehicle_id=UUID("00000000-0000-0000-0000-000000000001"),
                service_a_id=1,
                service_b_id=2,
                reason="same vehicle",
            )
        ],
        block_conflicts=[
            BlockConflict(
                block_id=UUID("00000000-0000-0000-0000-000000000002"),
                service_a_id=1,
                service_b_id=2,
                overlap_start=100,
                overlap_end=200,
            )
        ],
        interlocking_conflicts=[
            InterlockingConflict(
                group=1,
                block_a_id=UUID("00000000-0000-0000-0000-000000000003"),
                block_b_id=UUID("00000000-0000-0000-0000-000000000004"),
                service_a_id=1,
                service_b_id=2,
                overlap_start=300,
                overlap_end=400,
            )
        ],
        battery_conflicts=[
            BatteryConflict(type=BatteryConflictType.LOWBATTERY, service_id=1)
        ],
    )
    exc = ConflictError(conflicts)
    resp = await domain_error_handler(None, exc)

    assert resp.status_code == 409
    import json

    detail = json.loads(resp.body)["detail"]
    assert detail["message"] == "Service has scheduling conflicts"
    assert len(detail["vehicle_conflicts"]) == 1
    assert detail["vehicle_conflicts"][0]["reason"] == "same vehicle"
    assert len(detail["block_conflicts"]) == 1
    assert detail["block_conflicts"][0]["overlap_start"] == 100
    assert len(detail["interlocking_conflicts"]) == 1
    assert detail["interlocking_conflicts"][0]["group"] == 1
    assert len(detail["battery_conflicts"]) == 1
    assert detail["battery_conflicts"][0]["type"] == "LOWBATTERY"


async def test_conflict_error_with_empty_lists():
    conflicts = ServiceConflicts(
        vehicle_conflicts=[],
        block_conflicts=[],
        interlocking_conflicts=[],
        battery_conflicts=[],
    )
    exc = ConflictError(conflicts)
    resp = await domain_error_handler(None, exc)

    assert resp.status_code == 409
    import json

    detail = json.loads(resp.body)["detail"]
    assert detail["vehicle_conflicts"] == []
    assert detail["block_conflicts"] == []
    assert detail["interlocking_conflicts"] == []
    assert detail["battery_conflicts"] == []


async def test_unmapped_error_code_defaults_to_400():
    exc = DomainError(ErrorCode.EMPTY_SERVICE_NAME, "some validation error")
    # EMPTY_SERVICE_NAME is not in STATUS_MAP, so it defaults to 400.
    resp = await domain_error_handler(None, exc)
    assert resp.status_code == 400


async def test_error_response_schema_matches_structured_output():
    exc = DomainError(
        ErrorCode.SERVICE_NOT_FOUND,
        "Service 1 not found",
        {"service_id": 1},
    )
    resp = await domain_error_handler(None, exc)
    body = json.loads(resp.body)
    validated = ErrorResponse.model_validate(body)
    assert validated.detail.error_code == "SERVICE_NOT_FOUND"
    assert validated.detail.message == "Service 1 not found"
    assert validated.detail.context == {"service_id": 1}


async def test_conflict_detail_response_schema_matches_conflict_output():
    conflicts = ServiceConflicts(
        vehicle_conflicts=[
            VehicleConflict(
                vehicle_id=UUID("00000000-0000-0000-0000-000000000001"),
                service_a_id=1,
                service_b_id=2,
                reason="same vehicle",
            )
        ],
        block_conflicts=[
            BlockConflict(
                block_id=UUID("00000000-0000-0000-0000-000000000002"),
                service_a_id=1,
                service_b_id=2,
                overlap_start=100,
                overlap_end=200,
            )
        ],
        interlocking_conflicts=[
            InterlockingConflict(
                group=1,
                block_a_id=UUID("00000000-0000-0000-0000-000000000003"),
                block_b_id=UUID("00000000-0000-0000-0000-000000000004"),
                service_a_id=1,
                service_b_id=2,
                overlap_start=300,
                overlap_end=400,
            )
        ],
        battery_conflicts=[
            BatteryConflict(type=BatteryConflictType.LOWBATTERY, service_id=1)
        ],
    )
    exc = ConflictError(conflicts)
    resp = await domain_error_handler(None, exc)
    body = json.loads(resp.body)
    validated = ConflictDetailResponse.model_validate(body)
    assert validated.detail.message == "Service has scheduling conflicts"
    assert len(validated.detail.vehicle_conflicts) == 1
    assert len(validated.detail.block_conflicts) == 1
    assert len(validated.detail.interlocking_conflicts) == 1
    assert len(validated.detail.battery_conflicts) == 1


def test_openapi_schema_includes_error_responses():
    from main import app

    schema = app.openapi()
    paths = schema["paths"]

    # PATCH /api/services/{service_id}/route should have 400, 404, 409, 422
    route_update = paths["/api/services/{service_id}/route"]["patch"]["responses"]
    assert "400" in route_update
    assert "404" in route_update
    assert "409" in route_update
    assert "422" in route_update

    # GET /api/services/{service_id} should have 404
    get_service = paths["/api/services/{service_id}"]["get"]["responses"]
    assert "404" in get_service

    # POST /api/services should have 400
    create_service = paths["/api/services"]["post"]["responses"]
    assert "400" in create_service

    # DELETE /api/services/{service_id} should have 404
    delete_service = paths["/api/services/{service_id}"]["delete"]["responses"]
    assert "404" in delete_service

    # PATCH /api/blocks/{block_id} should have 404
    update_block = paths["/api/blocks/{block_id}"]["patch"]["responses"]
    assert "404" in update_block

    # POST /api/routes/validate should have 400, 422
    validate_route = paths["/api/routes/validate"]["post"]["responses"]
    assert "400" in validate_route
    assert "422" in validate_route

    # POST /api/schedules/generate should have 400
    generate_schedule = paths["/api/schedules/generate"]["post"]["responses"]
    assert "400" in generate_schedule

from __future__ import annotations

from uuid import UUID

from domain.domain_service.conflict.model import VehicleConflict
from domain.domain_service.conflict.shared import (
    ServiceEndpoints,
    ServiceWindow,
    find_time_overlaps,
)


def detect_vehicle_conflicts(
    vehicle_id: UUID,
    windows: list[ServiceWindow],
    endpoints: list[ServiceEndpoints],
) -> list[VehicleConflict]:
    return _detect_time_overlaps(
        vehicle_id, windows
    ) + _detect_location_discontinuities(vehicle_id, endpoints)


def _detect_time_overlaps(
    vehicle_id: UUID,
    windows: list[ServiceWindow],
) -> list[VehicleConflict]:
    return [
        VehicleConflict(
            vehicle_id, a.service_id, b.service_id, "Overlapping time windows"
        )
        for a, b in find_time_overlaps(windows)
    ]


def _detect_location_discontinuities(
    vehicle_id: UUID,
    endpoints: list[ServiceEndpoints],
) -> list[VehicleConflict]:
    conflicts: list[VehicleConflict] = []
    for i in range(1, len(endpoints)):
        prev, curr = endpoints[i - 1], endpoints[i]
        if curr.first_node_id != prev.last_node_id:
            conflicts.append(
                VehicleConflict(
                    vehicle_id,
                    prev.service_id,
                    curr.service_id,
                    "Location discontinuity",
                )
            )
    return conflicts

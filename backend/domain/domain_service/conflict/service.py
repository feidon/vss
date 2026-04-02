from __future__ import annotations

from domain.block.model import Block
from domain.domain_service.conflict.detection import (
    detect_battery_conflicts,
    detect_block_conflicts,
    detect_interlocking_conflicts,
    detect_location_discontinuity_conflicts,
    detect_time_overlap_conflicts,
)
from domain.domain_service.conflict.model import (
    InsufficientChargeConflict,
    LowBatteryConflict,
    ServiceConflicts,
)
from domain.domain_service.conflict.preparation import (
    build_battery_steps,
    build_occupancies,
    build_vehicle_schedule,
)
from domain.service.model import Service
from domain.vehicle.model import Vehicle


def detect_conflicts(
    candidate: Service,
    other_services: list[Service],
    blocks: list[Block],
    vehicles: list[Vehicle] | None = None,
) -> ServiceConflicts:
    """Check all conflicts for a candidate service against other services."""
    all_services = [s for s in other_services if s.id != candidate.id]
    all_services.append(candidate)

    schedule = build_vehicle_schedule(candidate.vehicle_id, all_services)
    block_occupancies, group_occupancies = build_occupancies(all_services, blocks)

    low_battery: list[LowBatteryConflict] = []
    insufficient_charge: list[InsufficientChargeConflict] = []
    if vehicles:
        vehicle_by_id = {v.id: v for v in vehicles}
        candidate_vehicle = vehicle_by_id.get(candidate.vehicle_id)
        if candidate_vehicle is not None:
            battery_steps = build_battery_steps(
                candidate_vehicle.id,
                all_services,
            )
            low_battery, insufficient_charge = detect_battery_conflicts(
                candidate_vehicle,
                battery_steps,
            )

    vehicle_conflicts = detect_time_overlap_conflicts(
        candidate.vehicle_id, schedule.windows
    ) + detect_location_discontinuity_conflicts(
        candidate.vehicle_id, schedule.endpoints
    )

    return ServiceConflicts(
        vehicle_conflicts=vehicle_conflicts,
        block_conflicts=detect_block_conflicts(block_occupancies),
        interlocking_conflicts=detect_interlocking_conflicts(group_occupancies),
        low_battery_conflicts=low_battery,
        insufficient_charge_conflicts=insufficient_charge,
    )

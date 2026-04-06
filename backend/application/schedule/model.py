from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from domain.shared.types import EpochSeconds


@dataclass(frozen=True)
class BlockTiming:
    """Occupancy interval for one block in a route variant, relative to trip departure."""

    block_id: UUID
    enter_offset: int  # seconds after trip departs yard
    exit_offset: int  # enter_offset + traversal_time


@dataclass(frozen=True)
class StationArrival:
    """When a trip visits a station, relative to trip departure."""

    station_name: str
    platform_id: UUID
    arrival_offset: int


@dataclass(frozen=True)
class RouteVariant:
    """One route pattern through the network with pre-computed timings.

    Produced by ``compute_route_variants`` and consumed by the solver.
    The solver treats variants as opaque data — it does not need to know
    which decision points produced any particular variant, only the
    block timings, cycle time, and stop sequence.
    """

    index: int
    stop_ids: list[UUID]  # ordered platform/yard IDs for build_full_route
    block_timings: list[BlockTiming]
    station_arrivals: list[StationArrival]  # 2 per station (outbound + return)
    cycle_time: int  # total seconds from yard departure to yard arrival
    num_blocks: int


@dataclass(frozen=True)
class SolverInput:
    """Everything the solver needs - no domain objects."""

    variants: list[RouteVariant]
    num_vehicles: int
    vehicle_ids: list[UUID]
    start_time: int  # epoch seconds
    end_time: int  # epoch seconds
    departure_gap_seconds: int
    interlocking_groups: dict[int, list[UUID]]  # group_id -> block_ids


@dataclass(frozen=True)
class TripAssignment:
    """Solver output for one trip."""

    vehicle_index: int
    depart_time: EpochSeconds  # absolute epoch seconds
    variant_index: int


@dataclass(frozen=True)
class SolverOutput:
    """Complete solver result."""

    assignments: list[TripAssignment]

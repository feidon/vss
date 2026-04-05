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
    """One of the 8 possible route patterns through the network."""

    index: int
    s1_out: int  # 0=P1A, 1=P1B
    s3: int  # 0=P3A, 1=P3B
    s1_ret: int  # 0=P1A, 1=P1B
    stop_ids: list[UUID]  # ordered platform/yard IDs for build_full_route
    block_timings: list[BlockTiming]
    station_arrivals: list[StationArrival]  # 2 per station (outbound + return)
    cycle_time: int  # total seconds from yard departure to yard arrival
    num_blocks: int


@dataclass(frozen=True)
class SolverInput:
    """Everything the CP-SAT solver needs - no domain objects."""

    variants: list[RouteVariant]
    num_vehicles: int
    vehicle_ids: list[UUID]
    tile_period: int  # seconds; max(cycle_time + yard_dwell) across variants
    interval_seconds: int
    min_yard_dwells: list[int]  # per variant index
    cycle_times: list[int]  # per variant index
    interlocking_groups: dict[int, list[UUID]]  # group_id -> block_ids


@dataclass(frozen=True)
class TripAssignment:
    """Solver output for one trip."""

    vehicle_index: int
    trip_index: int
    depart_time: EpochSeconds
    variant_index: int


@dataclass(frozen=True)
class SolverOutput:
    """Complete solver result."""

    assignments: list[TripAssignment]

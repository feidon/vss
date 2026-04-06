from __future__ import annotations

from itertools import product

from domain.block.model import Block
from domain.domain_service.route_builder import build_full_route
from domain.network.model import NodeConnection, NodeType
from domain.station.model import Station

from application.schedule.model import (
    BlockTiming,
    RouteVariant,
    StationArrival,
)
from application.schedule.network_layout import build_network_layout


def compute_route_variants(
    stations: list[Station],
    blocks: list[Block],
    connections: frozenset[NodeConnection],
    dwell_time_seconds: int,
) -> list[RouteVariant]:
    layout = build_network_layout(stations)
    station_by_platform_id_dict = {p.id: s for s in stations for p in s.platforms}
    variants: list[RouteVariant] = []

    combinations = product(
        layout.endpoint_platforms,  # outbound S1 choice
        layout.turnaround_platforms,  # turnaround S3 choice
        layout.endpoint_platforms,  # return S1 choice
    )

    for index, (out_ep, turn, ret_ep) in enumerate(combinations):
        stop_ids = [
            layout.yard.id,
            out_ep.id,
            layout.middle_outbound.id,
            turn.id,
            layout.middle_return.id,
            ret_ep.id,
            layout.yard.id,
        ]
        dwell_by_stop = {sid: dwell_time_seconds for sid in stop_ids}
        dwell_by_stop[layout.yard.id] = 0  # yard dwell handled by solver

        route, timetable = build_full_route(
            stop_ids, dwell_by_stop, 0, connections, stations, blocks
        )

        block_timings: list[BlockTiming] = []
        station_arrivals: list[StationArrival] = []
        num_blocks = 0

        for node, entry in zip(route, timetable):
            if node.type == NodeType.BLOCK:
                block_timings.append(
                    BlockTiming(
                        block_id=node.id,
                        enter_offset=entry.arrival,
                        exit_offset=entry.departure,
                    )
                )
                num_blocks += 1
            elif node.type == NodeType.PLATFORM:
                station = station_by_platform_id_dict[node.id]
                station_arrivals.append(
                    StationArrival(
                        station_name=station.name,
                        platform_id=node.id,
                        arrival_offset=entry.arrival,
                    )
                )

        cycle_time = timetable[-1].departure  # departure from final yard node

        variants.append(
            RouteVariant(
                index=index,
                stop_ids=stop_ids,
                block_timings=block_timings,
                station_arrivals=station_arrivals,
                cycle_time=cycle_time,
                num_blocks=num_blocks,
            )
        )

    return variants

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


def compute_route_variants(
    stations: list[Station],
    blocks: list[Block],
    connections: frozenset[NodeConnection],
    dwell_time_seconds: int,
) -> list[RouteVariant]:
    yard = next(s for s in stations if s.is_yard)
    platform_by_name = {p.name: p for s in stations for p in s.platforms}
    station_by_platform_id = {p.id: s for s in stations for p in s.platforms}
    variants: list[RouteVariant] = []

    for index, (s1_out, s3_choice, s1_ret) in enumerate(product(range(2), repeat=3)):
        out_p1 = platform_by_name["P1B" if s1_out else "P1A"]
        p2a = platform_by_name["P2A"]
        s3_plat = platform_by_name["P3B" if s3_choice else "P3A"]
        p2b = platform_by_name["P2B"]
        ret_p1 = platform_by_name["P1B" if s1_ret else "P1A"]

        stop_ids = [yard.id, out_p1.id, p2a.id, s3_plat.id, p2b.id, ret_p1.id, yard.id]
        dwell_by_stop = {sid: dwell_time_seconds for sid in stop_ids}
        dwell_by_stop[yard.id] = 0  # yard dwell handled by solver

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
                station = station_by_platform_id[node.id]
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
                s1_out=s1_out,
                s3=s3_choice,
                s1_ret=s1_ret,
                stop_ids=stop_ids,
                block_timings=block_timings,
                station_arrivals=station_arrivals,
                cycle_time=cycle_time,
                num_blocks=num_blocks,
            )
        )

    return variants

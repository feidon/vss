from __future__ import annotations

from uuid import UUID

from domain.block.model import Block
from domain.domain_service.route_finder import RouteFinder
from domain.error import DomainError, ErrorCode
from domain.network.model import Node, NodeConnection
from domain.service.model import TimetableEntry
from domain.shared.types import EpochSeconds
from domain.station.model import Platform, Station


def build_full_route(
    stop_ids: list[UUID],
    dwell_by_stop: dict[UUID, int],
    start_time: EpochSeconds,
    connections: frozenset[NodeConnection],
    stations: list[Station],
    blocks: list[Block],
) -> tuple[list[Node], list[TimetableEntry]]:
    platform_dict = {p.id: p for s in stations for p in s.platforms}
    yard_dict = {s.id: s for s in stations if s.is_yard}
    block_dict = {b.id: b for b in blocks}

    _validate_stops(stop_ids, platform_dict, yard_dict)

    full_path_ids = RouteFinder.build_full_path(
        stop_ids, connections, {b.id for b in blocks}
    )

    full_route = _resolve_nodes(full_path_ids, platform_dict, yard_dict, block_dict)

    timetable = _compute_timetable(
        full_route, platform_dict, yard_dict, block_dict, dwell_by_stop, start_time
    )

    return full_route, timetable


def _validate_stops(
    stop_ids: list[UUID],
    platform_dict: dict[UUID, Platform],
    yard_dict: dict[UUID, Station],
) -> None:
    valid_ids = set(platform_dict.keys()) | set(yard_dict.keys())
    for stop_id in stop_ids:
        if stop_id not in valid_ids:
            raise DomainError(ErrorCode.VALIDATION, f"Stop {stop_id} not found")


def _resolve_nodes(
    path_ids: list[UUID],
    platform_dict: dict[UUID, Platform],
    yard_dict: dict[UUID, Station],
    block_dict: dict[UUID, Block],
) -> list[Node]:
    nodes: list[Node] = []
    for nid in path_ids:
        if nid in block_dict:
            nodes.append(block_dict[nid].to_node())
        elif nid in platform_dict:
            nodes.append(platform_dict[nid].to_node())
        elif nid in yard_dict:
            nodes.append(yard_dict[nid].to_node())
        else:
            raise DomainError(ErrorCode.VALIDATION, f"Unknown node {nid} in path")
    return nodes


def _compute_timetable(
    full_path: list[Node],
    platform_dict: dict[UUID, Platform],
    yard_dict: dict[UUID, Station],
    block_dict: dict[UUID, Block],
    dwell_by_stop: dict[UUID, int],
    start_time: EpochSeconds,
) -> list[TimetableEntry]:
    entries: list[TimetableEntry] = []
    current_time = start_time

    for order, node in enumerate(full_path):
        if node.id in block_dict:
            entry = block_dict[node.id].to_timetable_entry(order, current_time)
        elif node.id in platform_dict:
            dwell = dwell_by_stop.get(node.id, 0)
            entry = platform_dict[node.id].to_timetable_entry(
                order, current_time, dwell
            )
        elif node.id in yard_dict:
            dwell = dwell_by_stop.get(node.id, 0)
            entry = yard_dict[node.id].to_timetable_entry(order, current_time, dwell)
        else:
            raise DomainError(
                ErrorCode.VALIDATION, f"Unknown node {node.id} in timetable"
            )
        entries.append(entry)
        current_time = entry.departure

    return entries

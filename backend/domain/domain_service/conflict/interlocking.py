from __future__ import annotations

from domain.domain_service.conflict.model import InterlockingConflict
from domain.domain_service.conflict.shared import GroupOccupancy, find_time_overlaps


def detect_interlocking_conflicts(
    by_group: dict[int, list[GroupOccupancy]],
) -> list[InterlockingConflict]:
    """Detect different blocks in the same interlocking group
    occupied by different services at overlapping times."""
    conflicts: list[InterlockingConflict] = []
    for group, occupancies in by_group.items():
        if group == 0:
            continue  # group 0 means "no interlocking group"
        for a, b in find_time_overlaps(occupancies):
            if a.block_id == b.block_id:
                continue  # already caught by block conflict detection
            conflicts.append(_interlocking_conflict_from_overlap(group, a, b))
    return conflicts


def _interlocking_conflict_from_overlap(
    group: int, a: GroupOccupancy, b: GroupOccupancy
) -> InterlockingConflict:
    return InterlockingConflict(
        group=group,
        block_a_id=a.block_id,
        block_b_id=b.block_id,
        service_a_id=a.service_id,
        service_b_id=b.service_id,
        overlap_start=b.arrival,
        overlap_end=a.departure,
    )

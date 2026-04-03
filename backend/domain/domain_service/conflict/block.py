from __future__ import annotations

from uuid import UUID

from domain.domain_service.conflict.model import BlockConflict
from domain.domain_service.conflict.shared import BlockOccupancy, find_time_overlaps


def detect_block_conflicts(
    by_block: dict[UUID, list[BlockOccupancy]],
) -> list[BlockConflict]:
    conflicts: list[BlockConflict] = []
    for block_id, occupancies in by_block.items():
        for a, b in find_time_overlaps(occupancies):
            conflicts.append(_block_conflict_from_overlap(block_id, a, b))
    return conflicts


def _block_conflict_from_overlap(
    block_id: UUID, a: BlockOccupancy, b: BlockOccupancy
) -> BlockConflict:
    return BlockConflict(
        block_id=block_id,
        service_a_id=a.service_id,
        service_b_id=b.service_id,
        overlap_start=b.arrival,
        overlap_end=a.departure,
    )

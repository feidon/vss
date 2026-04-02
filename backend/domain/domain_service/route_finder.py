from __future__ import annotations

from collections import deque
from uuid import UUID

from domain.error import DomainError, ErrorCode
from domain.network.model import NodeConnection


class RouteFinder:
    @staticmethod
    def find_block_chain(
        from_id: UUID,
        to_id: UUID,
        connections: frozenset[NodeConnection],
        block_ids: set[UUID],
    ) -> list[UUID]:
        """Return ordered block IDs between two platforms (exclusive of endpoints).

        BFS through block nodes only. Raises ValueError if no path exists.
        """
        adjacency: dict[UUID, list[UUID]] = {}
        for c in connections:
            adjacency.setdefault(c.from_id, []).append(c.to_id)

        queue: deque[tuple[UUID, list[UUID]]] = deque()
        visited: set[UUID] = set()

        for neighbor in adjacency.get(from_id, []):
            if neighbor == to_id:
                return []
            if neighbor in block_ids:
                queue.append((neighbor, [neighbor]))
                visited.add(neighbor)

        while queue:
            current, path = queue.popleft()
            for neighbor in adjacency.get(current, []):
                if neighbor == to_id:
                    return path
                if neighbor in block_ids and neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))

        raise DomainError(ErrorCode.NO_ROUTE, f"No route from {from_id} to {to_id}")

    @classmethod
    def build_full_path(
        cls,
        stop_ids: list[UUID],
        connections: frozenset[NodeConnection],
        block_ids: set[UUID],
    ) -> list[UUID]:
        """Build complete path including platforms and inferred blocks.

        Example: [P1A, P2A, P3A] -> [P1A, B3, B5, P2A, B6, B7, P3A]
        """
        if len(stop_ids) < 2:
            raise DomainError(ErrorCode.VALIDATION, "At least two stops are required")

        result: list[UUID] = [stop_ids[0]]
        for i in range(len(stop_ids) - 1):
            blocks = cls.find_block_chain(
                stop_ids[i], stop_ids[i + 1], connections, block_ids
            )
            result.extend(blocks)
            result.append(stop_ids[i + 1])
        return result

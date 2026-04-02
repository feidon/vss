from __future__ import annotations

from uuid import UUID

from application.graph.node_layout_repository import NodeLayoutRepository


class InMemoryNodeLayoutRepository(NodeLayoutRepository):
    def __init__(self, layouts: dict[UUID, tuple[float, float]] | None = None) -> None:
        self._layouts: dict[UUID, tuple[float, float]] = dict(layouts) if layouts else {}

    async def find_all(self) -> dict[UUID, tuple[float, float]]:
        return dict(self._layouts)

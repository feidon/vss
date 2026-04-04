from __future__ import annotations

from uuid import UUID

from domain.read_model.layout import LayoutData, LayoutRepository


class InMemoryLayoutRepository(LayoutRepository):
    def __init__(
        self,
        positions: dict[UUID, tuple[float, float]] | None = None,
        junction_blocks: dict[tuple[UUID, UUID], UUID] | None = None,
    ) -> None:
        self._positions = dict(positions) if positions else {}
        self._junction_blocks = dict(junction_blocks) if junction_blocks else {}

    async def find_all(self) -> LayoutData:
        return LayoutData(
            positions=dict(self._positions),
            junction_blocks=dict(self._junction_blocks),
        )

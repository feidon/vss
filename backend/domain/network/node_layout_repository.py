from abc import ABC, abstractmethod
from uuid import UUID


class NodeLayoutRepository(ABC):
    @abstractmethod
    async def find_all(self) -> dict[UUID, tuple[float, float]]:
        """Return {node_id: (x, y)} for all nodes with layout data."""

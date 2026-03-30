from dataclasses import dataclass
from uuid import UUID

@dataclass
class Block:
    id: UUID
    name: str
    group: int
    traversal_time: int

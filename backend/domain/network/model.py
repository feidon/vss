from dataclasses import dataclass
from enum import Enum
from uuid import UUID


class NodeType(Enum):
    BLOCK = "block"
    PLATFORM = "platform"


@dataclass(frozen=True)
class Node:
    id: UUID
    type: NodeType


@dataclass(frozen=True)
class NodeConnection:
    from_id: UUID
    to_id: UUID

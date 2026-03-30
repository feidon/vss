from dataclasses import dataclass
from uuid import UUID

@dataclass
class Vehicle:
    id: UUID
    name: str
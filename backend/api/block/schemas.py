from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field

from domain.block.model import Block


class UpdateBlockRequest(BaseModel):
    traversal_time_seconds: int = Field(gt=0)


class BlockIdResponse(BaseModel):
    id: UUID


class BlockResponse(BaseModel):
    id: UUID
    name: str
    group: int
    traversal_time_seconds: int

    @classmethod
    def from_domain(cls, block: Block) -> BlockResponse:
        return cls(
            id=block.id,
            name=block.name,
            group=block.group,
            traversal_time_seconds=block.traversal_time_seconds,
        )

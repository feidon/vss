from uuid import uuid7

import pytest
from domain.block.model import Block
from domain.error import DomainError
from domain.network.model import NodeType


class TestBlock:
    def test_create_block(self):
        block = Block(id=uuid7(), name="B1", group=1, traversal_time_seconds=30)
        assert block.name == "B1"
        assert block.group == 1
        assert block.traversal_time_seconds == 30

    def test_rejects_zero_traversal_time(self):
        with pytest.raises(
            DomainError, match="traversal_time_seconds must be positive"
        ):
            Block(id=uuid7(), name="B1", group=1, traversal_time_seconds=0)

    def test_rejects_negative_traversal_time(self):
        with pytest.raises(
            DomainError, match="traversal_time_seconds must be positive"
        ):
            Block(id=uuid7(), name="B1", group=1, traversal_time_seconds=-5)

    def test_to_node(self):
        block = Block(id=uuid7(), name="B1", group=1, traversal_time_seconds=30)
        node = block.to_node()
        assert node.id == block.id
        assert node.type == NodeType.BLOCK

    def test_equality_by_id(self):
        bid = uuid7()
        b1 = Block(id=bid, name="A", group=1, traversal_time_seconds=10)
        b2 = Block(id=bid, name="B", group=2, traversal_time_seconds=20)
        assert b1 == b2

    def test_inequality_by_id(self):
        b1 = Block(id=uuid7(), name="B1", group=1, traversal_time_seconds=10)
        b2 = Block(id=uuid7(), name="B1", group=1, traversal_time_seconds=10)
        assert b1 != b2

    def test_hashable(self):
        bid = uuid7()
        b1 = Block(id=bid, name="A", group=1, traversal_time_seconds=10)
        b2 = Block(id=bid, name="B", group=2, traversal_time_seconds=20)
        assert {b1, b2} == {b1}

    def test_update_traversal_time(self):
        block = Block(id=uuid7(), name="B1", group=1, traversal_time_seconds=30)
        block.update_traversal_time(60)
        assert block.traversal_time_seconds == 60

    def test_update_traversal_time_rejects_invalid(self):
        block = Block(id=uuid7(), name="B1", group=1, traversal_time_seconds=30)
        with pytest.raises(
            DomainError, match="traversal_time_seconds must be positive"
        ):
            block.update_traversal_time(0)

    def test_to_timetable_entry(self):
        block = Block(id=uuid7(), name="B1", group=1, traversal_time_seconds=30)
        entry = block.to_timetable_entry(order=0, arrival=100)
        assert entry.node_id == block.id
        assert entry.order == 0
        assert entry.arrival == 100
        assert entry.departure == 130

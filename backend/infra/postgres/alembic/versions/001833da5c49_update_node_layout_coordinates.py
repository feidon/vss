"""update node layout coordinates

Revision ID: 001833da5c49
Revises: 7b68506b7d08
Create Date: 2026-04-04

"""

from collections.abc import Sequence

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = "001833da5c49"
down_revision: str | Sequence[str] | None = "7b68506b7d08"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# New coordinates keyed by node name.
_BLOCK_COORDS: dict[str, tuple[float, float]] = {
    "B1": (850.0, 60.0),
    "B2": (850.0, 140.0),
    "B3": (650.0, 40.0),
    "B4": (550.0, 80.0),
    "B5": (510.0, 40.0),
    "B6": (300.0, 40.0),
    "B7": (160.0, 40.0),
    "B8": (200.0, 80.0),
    "B9": (160.0, 160.0),
    "B10": (200.0, 120.0),
    "B11": (300.0, 160.0),
    "B12": (510.0, 160.0),
    "B13": (650.0, 160.0),
    "B14": (550.0, 120.0),
}

_PLATFORM_COORDS: dict[str, tuple[float, float]] = {
    "P1A": (750.0, 40.0),
    "P1B": (750.0, 160.0),
    "P2A": (400.0, 40.0),
    "P2B": (400.0, 160.0),
    "P3A": (50.0, 40.0),
    "P3B": (50.0, 160.0),
}

_YARD_COORDS: tuple[float, float] = (950.0, 100.0)


def upgrade() -> None:
    conn = op.get_bind()

    for name, (x, y) in _BLOCK_COORDS.items():
        conn.execute(
            text(
                "UPDATE node_layouts SET x = :x, y = :y "
                "WHERE node_id = (SELECT id FROM blocks WHERE name = :name)"
            ),
            {"x": x, "y": y, "name": name},
        )

    for name, (x, y) in _PLATFORM_COORDS.items():
        conn.execute(
            text(
                "UPDATE node_layouts SET x = :x, y = :y "
                "WHERE node_id = (SELECT id FROM platforms WHERE name = :name)"
            ),
            {"x": x, "y": y, "name": name},
        )

    conn.execute(
        text(
            "UPDATE node_layouts SET x = :x, y = :y "
            "WHERE node_id = (SELECT id FROM stations WHERE is_yard = true)"
        ),
        {"x": _YARD_COORDS[0], "y": _YARD_COORDS[1]},
    )


def downgrade() -> None:
    _OLD_BLOCK_COORDS: dict[str, tuple[float, float]] = {
        "B1": (75.0, 100.0),
        "B2": (75.0, 200.0),
        "B3": (225.0, 75.0),
        "B4": (225.0, 175.0),
        "B5": (300.0, 125.0),
        "B6": (450.0, 100.0),
        "B7": (525.0, 75.0),
        "B8": (525.0, 125.0),
        "B9": (525.0, 275.0),
        "B10": (525.0, 225.0),
        "B11": (450.0, 250.0),
        "B12": (300.0, 225.0),
        "B13": (225.0, 225.0),
        "B14": (225.0, 275.0),
    }
    _OLD_PLATFORM_COORDS: dict[str, tuple[float, float]] = {
        "P1A": (150.0, 100.0),
        "P1B": (150.0, 200.0),
        "P2A": (375.0, 100.0),
        "P2B": (375.0, 200.0),
        "P3A": (600.0, 75.0),
        "P3B": (600.0, 125.0),
    }
    _OLD_YARD_COORDS: tuple[float, float] = (0.0, 150.0)

    conn = op.get_bind()

    for name, (x, y) in _OLD_BLOCK_COORDS.items():
        conn.execute(
            text(
                "UPDATE node_layouts SET x = :x, y = :y "
                "WHERE node_id = (SELECT id FROM blocks WHERE name = :name)"
            ),
            {"x": x, "y": y, "name": name},
        )

    for name, (x, y) in _OLD_PLATFORM_COORDS.items():
        conn.execute(
            text(
                "UPDATE node_layouts SET x = :x, y = :y "
                "WHERE node_id = (SELECT id FROM platforms WHERE name = :name)"
            ),
            {"x": x, "y": y, "name": name},
        )

    conn.execute(
        text(
            "UPDATE node_layouts SET x = :x, y = :y "
            "WHERE node_id = (SELECT id FROM stations WHERE is_yard = true)"
        ),
        {"x": _OLD_YARD_COORDS[0], "y": _OLD_YARD_COORDS[1]},
    )

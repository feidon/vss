"""Seed data for the Vehicle Scheduling System track map.

Defines all blocks, stations, platforms, connections, and vehicles
according to the assignment specification.

Adjacency list (from requirement):
    Y  <- B1  -> P1A
    Y  <- B2  -> P1B
    P1A -> B3  -> B5  -> P2A
    P1B -> B4  -> B5  -> P2A
    P2A -> B6  -> B7  -> P3A
    P2A -> B6  -> B8  -> P3B
    P3A -> B10 -> B11 -> P2B
    P3B -> B9  -> B11 -> P2B
    P2B -> B12 -> B14 -> P1B
    P2B -> B12 -> B13 -> P1A

B1/B2 use `<-` notation indicating bidirectional connectivity
between the Yard and S1 platforms.  All other blocks are
strictly unidirectional as shown by `->`.
"""

from uuid import UUID, uuid7

from domain.block.model import Block
from domain.network.model import NodeConnection
from domain.station.model import Platform, Station
from domain.vehicle.model import Vehicle

# ── IDs ─────────────────────────────────────────────────────

YARD_ID = uuid7()

PLATFORM_ID_BY_NAME = {
    name: uuid7() for name in ["P1A", "P1B", "P2A", "P2B", "P3A", "P3B"]
}

BLOCK_ID_BY_NAME = {f"B{i}": uuid7() for i in range(1, 15)}

STATION_ID_BY_NAME = {
    "Y": YARD_ID,
    "S1": uuid7(),
    "S2": uuid7(),
    "S3": uuid7(),
}

VEHICLE_ID_BY_NAME = {name: uuid7() for name in ["V1", "V2", "V3"]}

# ── Interlocking groups ─────────────────────────────────────
#   Group 1: B1, B2
#   Group 2: B3, B4, B13, B14
#   Group 3: B7, B8, B9, B10
#   Group 0 (none): B5, B6, B11, B12

_BLOCK_GROUPS: dict[str, int] = {
    "B1": 1,
    "B2": 1,
    "B3": 2,
    "B4": 2,
    "B13": 2,
    "B14": 2,
    "B5": 0,
    "B6": 0,
    "B11": 0,
    "B12": 0,
    "B7": 3,
    "B8": 3,
    "B9": 3,
    "B10": 3,
}

_DEFAULT_TRAVERSAL_TIME = 30  # seconds

# ── Domain objects ──────────────────────────────────────────


def create_blocks() -> list[Block]:
    return [
        Block(
            id=BLOCK_ID_BY_NAME[name],
            name=name,
            group=_BLOCK_GROUPS[name],
            traversal_time_seconds=_DEFAULT_TRAVERSAL_TIME,
        )
        for name in [f"B{i}" for i in range(1, 15)]
    ]


def create_stations() -> list[Station]:
    return [
        Station(
            id=YARD_ID,
            name="Y",
            is_yard=True,
            platforms=[],
        ),
        Station(
            id=STATION_ID_BY_NAME["S1"],
            name="S1",
            is_yard=False,
            platforms=[
                Platform(id=PLATFORM_ID_BY_NAME["P1A"], name="P1A"),
                Platform(id=PLATFORM_ID_BY_NAME["P1B"], name="P1B"),
            ],
        ),
        Station(
            id=STATION_ID_BY_NAME["S2"],
            name="S2",
            is_yard=False,
            platforms=[
                Platform(id=PLATFORM_ID_BY_NAME["P2A"], name="P2A"),
                Platform(id=PLATFORM_ID_BY_NAME["P2B"], name="P2B"),
            ],
        ),
        Station(
            id=STATION_ID_BY_NAME["S3"],
            name="S3",
            is_yard=False,
            platforms=[
                Platform(id=PLATFORM_ID_BY_NAME["P3A"], name="P3A"),
                Platform(id=PLATFORM_ID_BY_NAME["P3B"], name="P3B"),
            ],
        ),
    ]


def create_connections() -> frozenset[NodeConnection]:
    """Build the directed connection graph from the adjacency list.

    B1 and B2 are bidirectional (Y <-> B1 <-> P1A, Y <-> B2 <-> P1B)
    to allow vehicles to depart from and return to the Yard.
    All other blocks are strictly unidirectional.
    """
    b = BLOCK_ID_BY_NAME
    p = PLATFORM_ID_BY_NAME
    y = YARD_ID

    edges: list[tuple[UUID, UUID]] = [
        # B1 / B2 — bidirectional between Yard and S1 platforms
        (y, b["B1"]),
        (b["B1"], p["P1A"]),
        (p["P1A"], b["B1"]),
        (b["B1"], y),
        (y, b["B2"]),
        (b["B2"], p["P1B"]),
        (p["P1B"], b["B2"]),
        (b["B2"], y),
        # S1 -> S2  (outbound)
        (p["P1A"], b["B3"]),
        (b["B3"], b["B5"]),
        (b["B5"], p["P2A"]),
        (p["P1B"], b["B4"]),
        (b["B4"], b["B5"]),
        # S2 -> S3
        (p["P2A"], b["B6"]),
        (b["B6"], b["B7"]),
        (b["B7"], p["P3A"]),
        (b["B6"], b["B8"]),
        (b["B8"], p["P3B"]),
        # S3 -> S2  (return)
        (p["P3A"], b["B10"]),
        (b["B10"], b["B11"]),
        (b["B11"], p["P2B"]),
        (p["P3B"], b["B9"]),
        (b["B9"], b["B11"]),
        # S2 -> S1  (return)
        (p["P2B"], b["B12"]),
        (b["B12"], b["B14"]),
        (b["B14"], p["P1B"]),
        (b["B12"], b["B13"]),
        (b["B13"], p["P1A"]),
    ]

    return frozenset(NodeConnection(from_id=f, to_id=t) for f, t in edges)


def create_vehicles() -> list[Vehicle]:
    return [
        Vehicle(id=VEHICLE_ID_BY_NAME["V1"], name="V1"),
        Vehicle(id=VEHICLE_ID_BY_NAME["V2"], name="V2"),
        Vehicle(id=VEHICLE_ID_BY_NAME["V3"], name="V3"),
    ]


def create_node_layouts() -> dict[UUID, tuple[float, float]]:
    b = BLOCK_ID_BY_NAME
    p = PLATFORM_ID_BY_NAME
    return {
        YARD_ID: (0.0, 150.0),
        b["B1"]: (75.0, 100.0),
        b["B2"]: (75.0, 200.0),
        p["P1A"]: (150.0, 100.0),
        p["P1B"]: (150.0, 200.0),
        b["B3"]: (225.0, 75.0),
        b["B4"]: (225.0, 175.0),
        b["B5"]: (300.0, 125.0),
        p["P2A"]: (375.0, 100.0),
        p["P2B"]: (375.0, 200.0),
        b["B6"]: (450.0, 100.0),
        b["B7"]: (525.0, 75.0),
        b["B8"]: (525.0, 125.0),
        p["P3A"]: (600.0, 75.0),
        p["P3B"]: (600.0, 125.0),
        b["B10"]: (525.0, 225.0),
        b["B9"]: (525.0, 275.0),
        b["B11"]: (450.0, 250.0),
        b["B12"]: (300.0, 225.0),
        b["B13"]: (225.0, 225.0),
        b["B14"]: (225.0, 275.0),
    }

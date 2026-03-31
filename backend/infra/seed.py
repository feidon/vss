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

from uuid import UUID, uuid5, NAMESPACE_DNS

from domain.block.model import Block
from domain.network.model import NodeConnection
from domain.station.model import Platform, Station
from domain.vehicle.model import Vehicle

# ── Deterministic UUID helper ───────────────────────────────

_NS = UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")


def _id(name: str) -> UUID:
    return uuid5(_NS, name)


# ── IDs ─────────────────────────────────────────────────────

YARD_ID = _id("Y")

PLATFORM_IDS = {
    "P1A": _id("P1A"),
    "P1B": _id("P1B"),
    "P2A": _id("P2A"),
    "P2B": _id("P2B"),
    "P3A": _id("P3A"),
    "P3B": _id("P3B"),
}

BLOCK_IDS = {f"B{i}": _id(f"B{i}") for i in range(1, 15)}

STATION_IDS = {
    "Y": YARD_ID,
    "S1": _id("S1"),
    "S2": _id("S2"),
    "S3": _id("S3"),
}

VEHICLE_IDS = {
    "V1": _id("V1"),
    "V2": _id("V2"),
    "V3": _id("V3"),
}

# ── Interlocking groups ─────────────────────────────────────
#   Group 1: B1, B2
#   Group 2: B3, B4, B13, B14
#   Group 3: B7, B8, B9, B10
#   Group 0 (none): B5, B6, B11, B12

_BLOCK_GROUPS: dict[str, int] = {
    "B1": 1, "B2": 1,
    "B3": 2, "B4": 2, "B13": 2, "B14": 2,
    "B5": 0, "B6": 0, "B11": 0, "B12": 0,
    "B7": 3, "B8": 3, "B9": 3, "B10": 3,
}

_DEFAULT_TRAVERSAL_TIME = 30  # seconds

# ── Domain objects ──────────────────────────────────────────


def create_blocks() -> list[Block]:
    return [
        Block(
            id=BLOCK_IDS[name],
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
            id=STATION_IDS["S1"],
            name="S1",
            is_yard=False,
            platforms=[
                Platform(id=PLATFORM_IDS["P1A"], name="P1A"),
                Platform(id=PLATFORM_IDS["P1B"], name="P1B"),
            ],
        ),
        Station(
            id=STATION_IDS["S2"],
            name="S2",
            is_yard=False,
            platforms=[
                Platform(id=PLATFORM_IDS["P2A"], name="P2A"),
                Platform(id=PLATFORM_IDS["P2B"], name="P2B"),
            ],
        ),
        Station(
            id=STATION_IDS["S3"],
            name="S3",
            is_yard=False,
            platforms=[
                Platform(id=PLATFORM_IDS["P3A"], name="P3A"),
                Platform(id=PLATFORM_IDS["P3B"], name="P3B"),
            ],
        ),
    ]


def create_connections() -> frozenset[NodeConnection]:
    """Build the directed connection graph from the adjacency list.

    B1 and B2 are bidirectional (Y <-> B1 <-> P1A, Y <-> B2 <-> P1B)
    to allow vehicles to depart from and return to the Yard.
    All other blocks are strictly unidirectional.
    """
    b = BLOCK_IDS
    p = PLATFORM_IDS
    y = YARD_ID

    edges: list[tuple[UUID, UUID]] = [
        # B1 / B2 — bidirectional between Yard and S1 platforms
        (y, b["B1"]),   (b["B1"], p["P1A"]),
        (p["P1A"], b["B1"]), (b["B1"], y),
        (y, b["B2"]),   (b["B2"], p["P1B"]),
        (p["P1B"], b["B2"]), (b["B2"], y),

        # S1 -> S2  (outbound)
        (p["P1A"], b["B3"]),  (b["B3"], b["B5"]),  (b["B5"], p["P2A"]),
        (p["P1B"], b["B4"]),  (b["B4"], b["B5"]),

        # S2 -> S3
        (p["P2A"], b["B6"]),
        (b["B6"], b["B7"]),   (b["B7"], p["P3A"]),
        (b["B6"], b["B8"]),   (b["B8"], p["P3B"]),

        # S3 -> S2  (return)
        (p["P3A"], b["B10"]), (b["B10"], b["B11"]), (b["B11"], p["P2B"]),
        (p["P3B"], b["B9"]),  (b["B9"], b["B11"]),

        # S2 -> S1  (return)
        (p["P2B"], b["B12"]),
        (b["B12"], b["B14"]), (b["B14"], p["P1B"]),
        (b["B12"], b["B13"]), (b["B13"], p["P1A"]),
    ]

    return frozenset(NodeConnection(from_id=f, to_id=t) for f, t in edges)


def create_vehicles() -> list[Vehicle]:
    return [
        Vehicle(id=VEHICLE_IDS["V1"], name="V1"),
        Vehicle(id=VEHICLE_IDS["V2"], name="V2"),
        Vehicle(id=VEHICLE_IDS["V3"], name="V3"),
    ]

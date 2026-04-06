"""Single source of truth for the schedule generator's network assumptions.

This module is the **one place** to read when you need to understand what
the schedule generator assumes about the underlying track network. All
topology-specific knowledge — station/platform identification, the trip
shape, the variant enumeration model, and the magic numbers used by the
solver and fleet-sizing logic — lives here. Every other module in
``application/schedule/`` either imports from this file or stays
topology-agnostic.

Trip shape
----------
Every variant follows the same fixed sequence of seven nodes::

    Y → S1 → S2 → S3 → S2 → S1 → Y

with three binary decision points (one per non-fixed stop):

==============  ============  ====================================
Decision        Choices       Why
==============  ============  ====================================
Outbound S1     P1A or P1B    Both reachable from yard via B1/B2
Turnaround S3   P3A or P3B    Both reachable from P2A via B6→B7/B8
Return S1       P1A or P1B    Both reachable from P2B via B12→B13/B14
==============  ============  ====================================

S2 has **no choice** because the tracks are physically directional:

* Outbound traffic on B5 only reaches P2A
* Return traffic on B11 only reaches P2B

Total variants: ``2 × 2 × 2 = 8``.

If the network topology changes
-------------------------------
1. Update the trip shape described above.
2. Update :func:`build_network_layout` to resolve the new stations/platforms.
3. Update the variant enumeration in
   :func:`application.schedule.route_variant.compute_route_variants` if the
   number or shape of decision points changes.
4. Update the assertions in :func:`build_network_layout` to match the new
   expected shape.
"""

from __future__ import annotations

from dataclasses import dataclass

from domain.station.model import Platform, Station
from domain.vehicle.model import CHARGE_SECONDS_PER_PERCENT, TRAVERSAL_DRAIN

# ── Station identity in the fixed network ────────────────────
# These are the names of the three non-yard stations the schedule
# generator looks up when building the route layout. Renaming any of
# them in the seed requires updating the matching constant here.
ENDPOINT_STATION_NAME = "S1"  # trip start and end (passenger origin/destination)
MIDDLE_STATION_NAME = "S2"  # pass-through, directional
TURNAROUND_STATION_NAME = "S3"  # reversal point

# ── Middle-station platform roles ────────────────────────────
# S2 has exactly two platforms; in the seed they are stored in
# outbound-then-return order (P2A first, P2B second). Outbound traffic
# arriving on B5 only reaches index 0; return traffic arriving on B11
# only reaches index 1.
MIDDLE_OUTBOUND_PLATFORM_INDEX = 0
MIDDLE_RETURN_PLATFORM_INDEX = 1

# ── Vehicle recharge requirement ─────────────────────────────
# Each block traversal drains TRAVERSAL_DRAIN% of battery, and recharging
# 1% of battery requires CHARGE_SECONDS_PER_PERCENT seconds of yard dwell.
# So a trip of N blocks needs at least N * SECONDS_TO_RECHARGE_PER_BLOCK
# seconds at the yard before the vehicle is allowed to depart again.
SECONDS_TO_RECHARGE_PER_BLOCK = TRAVERSAL_DRAIN * CHARGE_SECONDS_PER_PERCENT

# ── Fleet sizing tolerance ───────────────────────────────────
# num_vehicles = ceil(max_turnaround / interval) + FLEET_BUFFER
#
# The +1 is a safety buffer that absorbs rounding and timing slack so
# the scheduler never leaves a departure slot empty due to a vehicle
# being fractionally unavailable. See ``README.md`` > Assumptions >
# Domain.
FLEET_BUFFER = 1


@dataclass(frozen=True)
class NetworkLayout:
    """Resolved station and platform references for the fixed topology.

    Built once per ``compute_route_variants`` call via
    :func:`build_network_layout`. All trip building downstream uses these
    references directly — no string lookups, no platform-name dicts, no
    indexing into platform lists outside this module.
    """

    yard: Station
    endpoint_platforms: list[Platform]  # S1: both are decision options
    middle_outbound: Platform  # P2A: fixed outbound side of S2
    middle_return: Platform  # P2B: fixed return side of S2
    turnaround_platforms: list[Platform]  # S3: both are decision options


def build_network_layout(stations: list[Station]) -> NetworkLayout:
    """Resolve the fixed-topology station and platform references.

    Looks up S1/S2/S3 by name and pulls the platforms in seed order.
    Asserts the expected shape (one yard, two platforms per non-yard
    station) so a drift in the seed fails fast at the start of schedule
    generation rather than producing weird downstream errors.
    """
    by_name = {s.name: s for s in stations}
    yard = next(s for s in stations if s.is_yard)

    endpoint = by_name[ENDPOINT_STATION_NAME]
    middle = by_name[MIDDLE_STATION_NAME]
    turnaround = by_name[TURNAROUND_STATION_NAME]

    assert len(endpoint.platforms) == 2, (
        f"{ENDPOINT_STATION_NAME} must have exactly 2 platforms, "
        f"got {len(endpoint.platforms)}"
    )
    assert len(middle.platforms) == 2, (
        f"{MIDDLE_STATION_NAME} must have exactly 2 platforms, "
        f"got {len(middle.platforms)}"
    )
    assert len(turnaround.platforms) == 2, (
        f"{TURNAROUND_STATION_NAME} must have exactly 2 platforms, "
        f"got {len(turnaround.platforms)}"
    )

    return NetworkLayout(
        yard=yard,
        endpoint_platforms=endpoint.platforms,
        middle_outbound=middle.platforms[MIDDLE_OUTBOUND_PLATFORM_INDEX],
        middle_return=middle.platforms[MIDDLE_RETURN_PLATFORM_INDEX],
        turnaround_platforms=turnaround.platforms,
    )

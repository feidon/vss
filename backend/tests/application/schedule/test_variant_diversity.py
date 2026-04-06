"""Characterization tests for variant diversity and the feasible throughput ceiling.

These tests document *why* the schedule generator currently always picks
variant 0 under the default seed and what the minimum achievable departure
interval is **via the public API**. They guard against silent regressions
if the network topology or block traversal times drift.

API feasibility rules (from `ScheduleAppService._validate_request` and
`_compute_min_departure_gap`):
  1. `interval_seconds > 0`
  2. `dwell_time_seconds > 0`
  3. `effective_interval (= interval + dwell) >= min_departure_gap`

All solver inputs in this file respect these rules so results reflect
what a caller could actually observe through `generate_schedule`.

Key facts captured here:
  1. Under uniform 30s traversal, all 8 route variants have identical
     interlocking-group occupancy offsets. They are temporally
     indistinguishable to the solver, so first-fit always picks v0.
  2. The tightest feasible passenger interval under the default seed is
     60s (effective=75s, matching the 75s min_departure_gap). The
     resulting schedule is a uniform 75s cadence.
  3. Making traversal times heterogeneous across the P1A/P1B, P3A/P3B, and
     return-side decision points produces temporally distinct variants,
     and in a feasible interval window first-fit *does* pick multiple
     variants.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from uuid import UUID, uuid4

from application.schedule.model import SolverInput
from application.schedule.route_variant import compute_route_variants
from application.schedule.schedule_service import _compute_min_departure_gap
from application.schedule.solver import solve_schedule
from domain.block.model import Block
from infra.seed import (
    create_blocks,
    create_connections,
    create_stations,
    create_vehicles,
)


def _group_fingerprint(
    variant_block_timings, group_by_block: dict[UUID, int]
) -> tuple[tuple[int, tuple[tuple[int, int], ...]], ...]:
    """Return a hashable (group_id, sorted intervals) tuple for one variant."""
    by_group: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for bt in variant_block_timings:
        g = group_by_block.get(bt.block_id, 0)
        if g != 0:
            by_group[g].append((bt.enter_offset, bt.exit_offset))
    return tuple((g, tuple(sorted(by_group[g]))) for g in sorted(by_group))


def _override_traversal(blocks: list[Block], overrides: dict[str, int]) -> None:
    for b in blocks:
        if b.name in overrides:
            b.update_traversal_time(overrides[b.name])


def _build_feasible_solver_input(
    passenger_interval: int,
    dwell: int,
    overrides: dict[str, int] | None = None,
    end_time: int = 7200,
    num_vehicles: int = 20,
) -> SolverInput:
    """Build SolverInput matching `ScheduleAppService` feasibility rules.

    Asserts:
      - passenger_interval > 0       (API validation)
      - dwell > 0                    (API validation)
      - effective_interval (= passenger_interval + dwell) >= min_departure_gap
    """
    assert passenger_interval > 0, "API rule: interval_seconds must be positive"
    assert dwell > 0, "API rule: dwell_time_seconds must be positive"

    blocks = create_blocks()
    if overrides:
        _override_traversal(blocks, overrides)

    variants = compute_route_variants(
        stations=create_stations(),
        blocks=blocks,
        connections=create_connections(),
        dwell_time_seconds=dwell,
    )

    effective_interval = passenger_interval + dwell
    min_gap = _compute_min_departure_gap(variants, blocks)
    assert effective_interval >= min_gap, (
        f"infeasible input: passenger_interval={passenger_interval}, "
        f"dwell={dwell}, effective={effective_interval} < min_gap={min_gap}"
    )

    interlocking_groups: dict[int, list] = {}
    for b in blocks:
        if b.group != 0:
            interlocking_groups.setdefault(b.group, []).append(b.id)

    vehicle_ids = [v.id for v in create_vehicles()]
    while len(vehicle_ids) < num_vehicles:
        vehicle_ids.append(uuid4())

    return SolverInput(
        variants=variants,
        num_vehicles=num_vehicles,
        vehicle_ids=vehicle_ids[:num_vehicles],
        start_time=0,
        end_time=end_time,
        departure_gap_seconds=effective_interval,
        interlocking_groups=interlocking_groups,
    )


def _gaps(result) -> list[int]:
    times = sorted(a.depart_time for a in result.assignments)
    return [times[i + 1] - times[i] for i in range(len(times) - 1)]


class TestUniformTraversalVariantFingerprints:
    """At uniform 30s traversal, all 8 variants share one fingerprint."""

    def test_all_eight_variants_have_identical_interlocking_fingerprint(self):
        blocks = create_blocks()
        variants = compute_route_variants(
            stations=create_stations(),
            blocks=blocks,
            connections=create_connections(),
            dwell_time_seconds=15,
        )
        group_by_block = {b.id: b.group for b in blocks}

        fingerprints = {
            _group_fingerprint(v.block_timings, group_by_block) for v in variants
        }
        assert len(fingerprints) == 1, (
            f"Expected 1 fingerprint across 8 variants under uniform traversal, "
            f"got {len(fingerprints)}. This means variants became temporally "
            f"distinct — revisit the variant-diversity analysis."
        )

    def test_fingerprint_matches_known_offsets_at_dwell_15(self):
        """Lock in the exact offsets so drift in build_full_route is caught."""
        blocks = create_blocks()
        variants = compute_route_variants(
            stations=create_stations(),
            blocks=blocks,
            connections=create_connections(),
            dwell_time_seconds=15,
        )
        group_by_block = {b.id: b.group for b in blocks}

        fp = _group_fingerprint(variants[0].block_timings, group_by_block)
        assert fp == (
            (1, ((0, 30), (345, 375))),
            (2, ((45, 75), (300, 330))),
            (3, ((150, 180), (195, 225))),
        )


class TestSolverAlwaysPicksVariantZero:
    """Under the default seed at feasible intervals, first-fit locks on v0."""

    def test_variant_zero_picked_exclusively_at_feasible_intervals(self):
        # min_gap=75s at dwell=15, so passenger_interval must be >= 60
        # to keep effective >= 75. All four inputs below are feasible.
        for passenger_interval in [60, 75, 135, 285]:
            inp = _build_feasible_solver_input(
                passenger_interval=passenger_interval, dwell=15
            )
            result = solve_schedule(inp)
            variant_counts = Counter(a.variant_index for a in result.assignments)
            assert variant_counts and set(variant_counts) == {0}, (
                f"passenger_interval={passenger_interval}: expected exclusive "
                f"variant 0, got {dict(variant_counts)}"
            )


class TestBaselineThroughputCeiling:
    """The tightest feasible API input produces a uniform 75s cadence."""

    def test_tightest_feasible_request_yields_uniform_75s_gaps(self):
        """dwell=15, passenger_interval=60 → effective=75 = min_gap=75.

        This is the minimum passenger_interval the API allows at the default
        dwell, and it produces a perfectly regular 75s schedule.
        """
        inp = _build_feasible_solver_input(passenger_interval=60, dwell=15)
        result = solve_schedule(inp)

        gaps = _gaps(result)
        assert len(result.assignments) >= 90
        assert set(gaps) == {75}, f"expected uniform 75s gaps, got {sorted(set(gaps))}"

    def test_increasing_dwell_does_not_improve_baseline_via_api(self):
        """Bumping dwell cannot produce sub-75s gaps through the API.

        At dwell=60, the solver's internal min_departure_gap is 30s, but the
        API requires passenger_interval >= 1, forcing effective >= 61 and
        pushing the actual achieved gap *above* the dwell=15 baseline.
        """
        baseline = _build_feasible_solver_input(passenger_interval=60, dwell=15)
        bumped = _build_feasible_solver_input(passenger_interval=15, dwell=60)

        baseline_gaps = _gaps(solve_schedule(baseline))
        bumped_gaps = _gaps(solve_schedule(bumped))

        assert min(baseline_gaps) <= min(bumped_gaps), (
            f"baseline min gap {min(baseline_gaps)}s should be <= "
            f"dwell=60 min gap {min(bumped_gaps)}s"
        )


class TestHeterogeneousTraversalBreaksSymmetry:
    """Heterogeneous traversal times produce temporally distinct variants."""

    def test_s3_asymmetry_yields_two_fingerprint_classes(self):
        """Speeding up B8/B9 (P3B side) splits variants into fast/slow classes."""
        blocks = create_blocks()
        _override_traversal(blocks, {"B8": 15, "B9": 15})
        variants = compute_route_variants(
            stations=create_stations(),
            blocks=blocks,
            connections=create_connections(),
            dwell_time_seconds=15,
        )
        group_by_block = {b.id: b.group for b in blocks}

        fingerprints = {
            _group_fingerprint(v.block_timings, group_by_block) for v in variants
        }
        assert len(fingerprints) == 2, (
            f"Expected 2 fingerprint classes (P3A-turn vs P3B-turn), "
            f"got {len(fingerprints)}"
        )

    def test_full_asymmetry_yields_eight_distinct_fingerprints(self):
        """All three decision axes asymmetric → every variant uniquely distinct."""
        blocks = create_blocks()
        _override_traversal(
            blocks,
            {"B2": 20, "B4": 20, "B8": 20, "B9": 20, "B14": 20},
        )
        variants = compute_route_variants(
            stations=create_stations(),
            blocks=blocks,
            connections=create_connections(),
            dwell_time_seconds=15,
        )
        group_by_block = {b.id: b.group for b in blocks}

        fingerprints = {
            _group_fingerprint(v.block_timings, group_by_block) for v in variants
        }
        assert len(fingerprints) == 8

    def test_solver_diversifies_with_heterogeneous_traversal_at_feasible_interval(
        self,
    ):
        """S3 asymmetry + dwell=45 + passenger_interval=15 → multiple variants.

        With B8/B9 faster than B7/B10, min_gap at dwell=45 is 30s so
        effective=60 (passenger=15 + dwell=45) is feasible. In this interval
        window v0 self-conflicts often enough that first-fit naturally falls
        back to the faster P3B variants — no solver change needed.
        """
        inp = _build_feasible_solver_input(
            passenger_interval=15,
            dwell=45,
            overrides={"B8": 15, "B9": 15},
        )
        result = solve_schedule(inp)
        variant_counts = Counter(a.variant_index for a in result.assignments)
        assert len(variant_counts) >= 2, (
            f"Expected first-fit to diversify under heterogeneous traversal, "
            f"got {dict(variant_counts)}"
        )

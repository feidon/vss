from application.schedule.route_variant import compute_route_variants
from infra.seed import (
    BLOCK_ID_BY_NAME,
    create_blocks,
    create_connections,
    create_stations,
)


class TestComputeRouteVariants:
    def test_produces_eight_variants(self):
        variants = compute_route_variants(
            stations=create_stations(),
            blocks=create_blocks(),
            connections=create_connections(),
            dwell_time_seconds=30,
        )
        assert len(variants) == 8

    def test_all_variants_have_ten_blocks(self):
        variants = compute_route_variants(
            stations=create_stations(),
            blocks=create_blocks(),
            connections=create_connections(),
            dwell_time_seconds=30,
        )
        for v in variants:
            assert v.num_blocks == 10, f"Variant {v.index} has {v.num_blocks} blocks"

    def test_cycle_time_with_uniform_30s_blocks_and_30s_dwell(self):
        variants = compute_route_variants(
            stations=create_stations(),
            blocks=create_blocks(),
            connections=create_connections(),
            dwell_time_seconds=30,
        )
        # 10 blocks * 30s + 5 platform dwells * 30s = 450s
        for v in variants:
            assert v.cycle_time == 450, f"Variant {v.index}: {v.cycle_time}"

    def test_variant_zero_uses_p1a_and_p3a(self):
        variants = compute_route_variants(
            stations=create_stations(),
            blocks=create_blocks(),
            connections=create_connections(),
            dwell_time_seconds=30,
        )
        # Variant 0 corresponds to the first product() tuple — the
        # all-first-platform combination (P1A out, P3A turn, P1A ret).
        v0 = variants[0]
        block_ids = {bt.block_id for bt in v0.block_timings}
        assert BLOCK_ID_BY_NAME["B1"] in block_ids
        assert BLOCK_ID_BY_NAME["B3"] in block_ids
        assert BLOCK_ID_BY_NAME["B7"] in block_ids
        assert BLOCK_ID_BY_NAME["B13"] in block_ids
        assert BLOCK_ID_BY_NAME["B2"] not in block_ids
        assert BLOCK_ID_BY_NAME["B4"] not in block_ids

    def test_each_variant_has_five_station_arrivals(self):
        """Each trip visits 5 platforms: S1(out), S2A, S3, S2B, S1(ret)."""
        variants = compute_route_variants(
            stations=create_stations(),
            blocks=create_blocks(),
            connections=create_connections(),
            dwell_time_seconds=30,
        )
        for v in variants:
            assert len(v.station_arrivals) == 5, (
                f"Variant {v.index}: {len(v.station_arrivals)}"
            )

    def test_non_uniform_traversal_times(self):
        blocks = create_blocks()
        for b in blocks:
            if b.name == "B5":
                b.traversal_time_seconds = 60

        variants = compute_route_variants(
            stations=create_stations(),
            blocks=blocks,
            connections=create_connections(),
            dwell_time_seconds=30,
        )
        # 9 blocks * 30s + 1 block * 60s + 5 dwells * 30s = 270 + 60 + 150 = 480s
        for v in variants:
            assert v.cycle_time == 480, f"Variant {v.index}: {v.cycle_time}"

from infra.seed import (
    BLOCK_ID_BY_NAME,
    PLATFORM_ID_BY_NAME,
    STATION_ID_BY_NAME,
    VEHICLE_ID_BY_NAME,
    YARD_ID,
    create_blocks,
    create_connections,
    create_node_layouts,
    create_stations,
    create_vehicles,
)


class TestSeedBlocks:
    def test_creates_14_blocks(self):
        blocks = create_blocks()
        assert len(blocks) == 14

    def test_block_names_b1_through_b14(self):
        names = {b.name for b in create_blocks()}
        assert names == {f"B{i}" for i in range(1, 15)}

    def test_interlocking_groups(self):
        by_name = {b.name: b for b in create_blocks()}
        assert by_name["B1"].group == 1
        assert by_name["B2"].group == 1
        assert by_name["B3"].group == 2
        assert by_name["B4"].group == 2
        assert by_name["B13"].group == 2
        assert by_name["B14"].group == 2
        assert by_name["B7"].group == 3
        assert by_name["B8"].group == 3
        assert by_name["B9"].group == 3
        assert by_name["B10"].group == 3

    def test_default_traversal_time(self):
        for block in create_blocks():
            assert block.traversal_time_seconds == 30


class TestSeedStations:
    def test_creates_4_stations(self):
        stations = create_stations()
        assert len(stations) == 4

    def test_yard_is_marked(self):
        stations = create_stations()
        yard = next(s for s in stations if s.is_yard)
        assert yard.name == "Y"
        assert yard.id == YARD_ID
        assert yard.platforms == []

    def test_each_station_has_two_platforms(self):
        stations = create_stations()
        for s in stations:
            if not s.is_yard:
                assert len(s.platforms) == 2

    def test_platform_names(self):
        stations = create_stations()
        platform_names = {p.name for s in stations for p in s.platforms}
        assert platform_names == {"P1A", "P1B", "P2A", "P2B", "P3A", "P3B"}


class TestSeedConnections:
    def test_connections_not_empty(self):
        connections = create_connections()
        assert len(connections) > 0

    def test_outbound_path_y_to_p1a(self):
        """Y -> B1 -> P1A must be a valid path."""
        conns = {(c.from_id, c.to_id) for c in create_connections()}
        assert (YARD_ID, BLOCK_ID_BY_NAME["B1"]) in conns
        assert (BLOCK_ID_BY_NAME["B1"], PLATFORM_ID_BY_NAME["P1A"]) in conns

    def test_return_path_p1a_to_y(self):
        """P1A -> B1 -> Y must be a valid return path."""
        conns = {(c.from_id, c.to_id) for c in create_connections()}
        assert (PLATFORM_ID_BY_NAME["P1A"], BLOCK_ID_BY_NAME["B1"]) in conns
        assert (BLOCK_ID_BY_NAME["B1"], YARD_ID) in conns

    def test_loop_s1_to_s2_to_s3_and_back(self):
        conns = {(c.from_id, c.to_id) for c in create_connections()}
        # S1 -> S2
        assert (PLATFORM_ID_BY_NAME["P1A"], BLOCK_ID_BY_NAME["B3"]) in conns
        assert (BLOCK_ID_BY_NAME["B5"], PLATFORM_ID_BY_NAME["P2A"]) in conns
        # S2 -> S3
        assert (PLATFORM_ID_BY_NAME["P2A"], BLOCK_ID_BY_NAME["B6"]) in conns
        assert (BLOCK_ID_BY_NAME["B7"], PLATFORM_ID_BY_NAME["P3A"]) in conns
        # S3 -> S2 (return)
        assert (PLATFORM_ID_BY_NAME["P3A"], BLOCK_ID_BY_NAME["B10"]) in conns
        assert (BLOCK_ID_BY_NAME["B11"], PLATFORM_ID_BY_NAME["P2B"]) in conns
        # S2 -> S1 (return)
        assert (PLATFORM_ID_BY_NAME["P2B"], BLOCK_ID_BY_NAME["B12"]) in conns
        assert (BLOCK_ID_BY_NAME["B13"], PLATFORM_ID_BY_NAME["P1A"]) in conns


class TestSeedVehicles:
    def test_creates_3_vehicles(self):
        vehicles = create_vehicles()
        assert len(vehicles) == 3

    def test_vehicle_names(self):
        names = {v.name for v in create_vehicles()}
        assert names == {"V1", "V2", "V3"}


class TestSeedNodeLayouts:
    def test_creates_11_entries(self):
        """1 yard + 6 platforms + 4 junctions = 11 entries."""
        layouts = create_node_layouts()
        assert len(layouts) == 11

    def test_all_coordinates_are_non_negative_floats(self):
        layouts = create_node_layouts()
        for node_id, (x, y) in layouts.items():
            assert isinstance(x, float), f"x for {node_id} is not float"
            assert isinstance(y, float), f"y for {node_id} is not float"
            assert x >= 0.0, f"x for {node_id} is negative"
            assert y >= 0.0, f"y for {node_id} is negative"


class TestDeterministicIds:
    def test_ids_are_stable(self):
        """IDs must be deterministic across calls."""
        blocks_a = {b.id for b in create_blocks()}
        blocks_b = {b.id for b in create_blocks()}
        assert blocks_a == blocks_b

    def test_no_id_collisions_between_types(self):
        all_ids = (
            set(BLOCK_ID_BY_NAME.values())
            | set(PLATFORM_ID_BY_NAME.values())
            | set(STATION_ID_BY_NAME.values())
            | set(VEHICLE_ID_BY_NAME.values())
        )
        expected_count = (
            len(BLOCK_ID_BY_NAME)
            + len(PLATFORM_ID_BY_NAME)
            + len(STATION_ID_BY_NAME)
            + len(VEHICLE_ID_BY_NAME)
        )
        assert len(all_ids) == expected_count

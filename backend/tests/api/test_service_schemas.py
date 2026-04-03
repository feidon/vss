from uuid import uuid7

from api.service.schemas import ServiceResponse
from domain.network.model import Node, NodeType
from domain.service.model import Service, TimetableEntry
from domain.vehicle.model import Vehicle


def _vehicle(vid=None) -> Vehicle:
    vid = vid or uuid7()
    return Vehicle(id=vid, name="V1")


def _service_with_route() -> tuple[Service, dict]:
    p1_id, p2_id, b1_id = uuid7(), uuid7(), uuid7()
    route = [
        Node(id=p1_id, type=NodeType.PLATFORM),
        Node(id=b1_id, type=NodeType.BLOCK),
        Node(id=p2_id, type=NodeType.PLATFORM),
    ]
    timetable = [
        TimetableEntry(order=0, node_id=p1_id, arrival=1000, departure=1060),
        TimetableEntry(order=1, node_id=b1_id, arrival=1060, departure=1090),
        TimetableEntry(order=2, node_id=p2_id, arrival=1090, departure=1180),
    ]
    node_names = {p1_id: "P1A", b1_id: "B3", p2_id: "P2B"}
    service = Service(
        id=1, name="S1", vehicle_id=uuid7(), route=route, timetable=timetable
    )
    return service, node_names


class TestServiceResponseFromDomain:
    def test_with_route_and_timetable(self):
        service, node_names = _service_with_route()
        vehicle = _vehicle(service.vehicle_id)
        resp = ServiceResponse.from_domain(service, vehicle, node_names)

        assert resp.start_time == 1000
        assert resp.origin_name == "P1A"
        assert resp.destination_name == "P2B"

    def test_empty_route(self):
        vehicle = _vehicle()
        service = Service(
            id=2, name="S2", vehicle_id=vehicle.id, route=[], timetable=[]
        )
        resp = ServiceResponse.from_domain(service, vehicle, {})

        assert resp.start_time is None
        assert resp.origin_name is None
        assert resp.destination_name is None

    def test_destination_skips_trailing_blocks(self):
        """If route ends with blocks, destination is the last platform/yard."""
        p_id, b1_id, b2_id = uuid7(), uuid7(), uuid7()
        route = [
            Node(id=p_id, type=NodeType.PLATFORM),
            Node(id=b1_id, type=NodeType.BLOCK),
            Node(id=b2_id, type=NodeType.BLOCK),
        ]
        timetable = [
            TimetableEntry(order=0, node_id=p_id, arrival=100, departure=160),
            TimetableEntry(order=1, node_id=b1_id, arrival=160, departure=190),
            TimetableEntry(order=2, node_id=b2_id, arrival=190, departure=220),
        ]
        node_names = {p_id: "P1A", b1_id: "B1", b2_id: "B2"}
        service = Service(
            id=3, name="S3", vehicle_id=uuid7(), route=route, timetable=timetable
        )
        vehicle = _vehicle(service.vehicle_id)
        resp = ServiceResponse.from_domain(service, vehicle, node_names)

        assert resp.destination_name == "P1A"

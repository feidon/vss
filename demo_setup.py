#!/usr/bin/env python3
"""Set up demo services for conflict detection demonstration.

Creates background services and demo services pre-configured so the user
needs minimal actions (change time or add a few stops) to trigger each
of the 6 conflict types.

Usage:
    python3 demo_setup.py

Requires docker compose to be running (backend at http://localhost).
"""

import json
import sys
import urllib.request
from datetime import datetime

BASE_URL = "http://localhost/api"


def api(method: str, path: str, body: dict | None = None) -> dict | None:
    url = f"{BASE_URL}{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as resp:
            if resp.status == 204:
                return None
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        detail = json.loads(e.read()) if e.fp else {}
        print(f"  ERROR {e.code}: {method} {path}")
        print(f"  {json.dumps(detail, indent=2)}")
        sys.exit(1)
    except urllib.error.URLError:
        print("Cannot connect to backend at http://localhost")
        print("Make sure docker compose is running.")
        sys.exit(1)


def create_service(name: str, vehicle_id: str) -> int:
    result = api("POST", "/services", {"name": name, "vehicle_id": vehicle_id})
    return result["id"]


def set_route(service_id: int, stops: list[dict], start_time: int) -> None:
    api("PATCH", f"/services/{service_id}/route", {
        "stops": stops,
        "start_time": start_time,
    })


def main():
    print("Setting up demo services...\n")

    # ── Clean existing services ──────────────────────────────
    for svc in api("GET", "/services"):
        api("DELETE", f"/services/{svc['id']}")
        print(f"  Deleted: {svc['name']}")

    # ── Get vehicles & node UUIDs ────────────────────────────
    vehicles = api("GET", "/vehicles")
    v = {veh["name"]: veh["id"] for veh in vehicles}

    tmp = create_service("_tmp", v["V1"])
    detail = api("GET", f"/services/{tmp}")
    n = {node["name"]: node["id"] for node in detail["graph"]["nodes"]}
    api("DELETE", f"/services/{tmp}")

    # ── Base times (today, local timezone) ───────────────────
    today = datetime.now()
    t = lambda h, m=0: int(today.replace(hour=h, minute=m, second=0, microsecond=0).timestamp())

    # ═════════════════════════════════════════════════════════
    #  BACKGROUND SERVICES
    # ═════════════════════════════════════════════════════════

    # Express-A on V1: Y → P1A → P2A → P3A at 08:00
    sid = create_service("Express-A", v["V1"])
    set_route(sid, [
        {"node_id": n["Y"], "dwell_time": 60},
        {"node_id": n["P1A"], "dwell_time": 60},
        {"node_id": n["P2A"], "dwell_time": 60},
        {"node_id": n["P3A"], "dwell_time": 60},
    ], t(8))
    print("  Express-A (V1): Y->P1A->P2A->P3A @08:00")

    # Battery-Drain on V3: 6 loops P1A→P2A→P3A→P2B→P1A (48 blocks, 80%→32%)
    loop = [n["P1A"], n["P2A"], n["P3A"], n["P2B"]]
    drain_stops = []
    for i in range(6):
        start = 0 if i == 0 else 1  # first loop includes P1A, rest skip it
        for j in range(start, 4):
            drain_stops.append({"node_id": loop[j], "dwell_time": 10})
        drain_stops.append({"node_id": loop[0], "dwell_time": 10})

    sid = create_service("Battery-Drain", v["V3"])
    set_route(sid, drain_stops, t(14))
    print("  Battery-Drain (V3): 6 loops @14:00 (48 blocks, battery→32%)")

    # ═════════════════════════════════════════════════════════
    #  DEMO SERVICES
    # ═════════════════════════════════════════════════════════

    # 1. Block + Interlocking — pre-saved at safe time, user changes to 08:02
    sid = create_service("1. Block+Interlock [time→08:02]", v["V2"])
    set_route(sid, [
        {"node_id": n["P1B"], "dwell_time": 30},
        {"node_id": n["P2A"], "dwell_time": 30},
    ], t(9))
    print("  Demo 1 (V2): P1B->P2A @09:00 (pre-saved, change time to trigger)")

    # 2. Vehicle Overlap — pre-saved at safe time, user changes to 08:05
    sid = create_service("2. Vehicle Overlap [time→08:05]", v["V1"])
    set_route(sid, [
        {"node_id": n["P3A"], "dwell_time": 30},
        {"node_id": n["P2B"], "dwell_time": 30},
    ], t(9))
    print("  Demo 2 (V1): P3A->P2B @09:00 (pre-saved, change time to trigger)")

    # 3. Discontinuity — empty, user adds stops
    create_service("3. Discontinuity [+P1A→P2A @10:00]", v["V1"])
    print("  Demo 3 (V1): empty (add P1A→P2A @10:00)")

    # 4. Low Battery — empty, user adds stops
    create_service("4. Low Battery [+P1A→P2A→P3A @16:00]", v["V3"])
    print("  Demo 4 (V3): empty (add P1A→P2A→P3A @16:00)")

    # 5. Insufficient Charge — empty, user adds stops
    create_service("5. Insuf. Charge [+P1A→Y→P1A @16:00]", v["V3"])
    print("  Demo 5 (V3): empty (add P1A→Y→P1A @16:00)")

    # ── Print demo guide ─────────────────────────────────────
    print(f"""
============================================================
  DEMO GUIDE — 6 Conflict Types
============================================================

 1. Block + Interlocking  (just change time)
    Open "1. Block+Interlock" → change start to 08:02 → Update

 2. Vehicle Overlap  (just change time)
    Open "2. Vehicle Overlap" → change start to 08:05 → Update

 3. Discontinuity  (add 2 stops)
    Open "3. Discontinuity" → set 10:00 → click P1A, P2A → Update

 4. Low Battery  (add 3 stops)
    Open "4. Low Battery" → set 16:00 → click P1A, P2A, P3A → Update

 5. Insufficient Charge  (add 3 stops)
    Open "5. Insuf. Charge" → set 16:00 → click P1A, Y, P1A → Update

  NOTES
  - Demo 1 is fully independent
  - Demos 2 & 3 share V1 — demo one, then reset
  - Demos 4 & 5 share V3 — demo one, then reset
  - To reset: python3 demo_setup.py
============================================================""")


if __name__ == "__main__":
    main()

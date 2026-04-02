"""Seed the PostgreSQL database with the fixed track network.

Idempotent — uses ON CONFLICT DO NOTHING.
"""

from __future__ import annotations

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from infra.postgres.tables import (
    blocks_table,
    node_connections_table,
    node_layouts_table,
    platforms_table,
    stations_table,
    vehicles_table,
)
from infra.seed import (
    create_blocks,
    create_connections,
    create_node_layouts,
    create_stations,
    create_vehicles,
)


async def seed_database(session: AsyncSession) -> None:
    """Insert all reference data if not already present."""
    stations = create_stations()
    blocks = create_blocks()
    vehicles = create_vehicles()
    connections = create_connections()

    # Stations
    await session.execute(
        insert(stations_table)
        .values([{"id": s.id, "name": s.name, "is_yard": s.is_yard} for s in stations])
        .on_conflict_do_nothing(index_elements=["id"])
    )

    # Platforms
    platform_rows = [
        {"id": p.id, "name": p.name, "station_id": s.id}
        for s in stations
        for p in s.platforms
    ]
    if platform_rows:
        await session.execute(
            insert(platforms_table)
            .values(platform_rows)
            .on_conflict_do_nothing(index_elements=["id"])
        )

    # Blocks
    await session.execute(
        insert(blocks_table)
        .values(
            [
                {
                    "id": b.id,
                    "name": b.name,
                    "group": b.group,
                    "traversal_time_seconds": b.traversal_time_seconds,
                }
                for b in blocks
            ]
        )
        .on_conflict_do_nothing(index_elements=["id"])
    )

    # Vehicles
    await session.execute(
        insert(vehicles_table)
        .values([{"id": v.id, "name": v.name} for v in vehicles])
        .on_conflict_do_nothing(index_elements=["id"])
    )

    # Node connections
    await session.execute(
        insert(node_connections_table)
        .values([{"from_id": c.from_id, "to_id": c.to_id} for c in connections])
        .on_conflict_do_nothing()
    )

    # Node layouts
    layouts = create_node_layouts()
    await session.execute(
        insert(node_layouts_table)
        .values([{"node_id": nid, "x": x, "y": y} for nid, (x, y) in layouts.items()])
        .on_conflict_do_nothing(index_elements=["node_id"])
    )

    await session.commit()

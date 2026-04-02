from sqlalchemy import (
    Boolean,
    Column,
    Float,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB

metadata = MetaData()

stations_table = Table(
    "stations",
    metadata,
    Column("id", Uuid, primary_key=True),
    Column("name", String, nullable=False),
    Column("is_yard", Boolean, nullable=False),
)

platforms_table = Table(
    "platforms",
    metadata,
    Column("id", Uuid, primary_key=True),
    Column("name", String, nullable=False),
    Column("station_id", Uuid, ForeignKey("stations.id"), nullable=False),
)

blocks_table = Table(
    "blocks",
    metadata,
    Column("id", Uuid, primary_key=True),
    Column("name", String, nullable=False),
    Column("group", Integer, nullable=False),
    Column("traversal_time_seconds", Integer, nullable=False),
)

vehicles_table = Table(
    "vehicles",
    metadata,
    Column("id", Uuid, primary_key=True),
    Column("name", String, nullable=False),
)

services_table = Table(
    "services",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", String, nullable=False),
    Column("vehicle_id", Uuid, ForeignKey("vehicles.id"), nullable=False),
    Column("route", JSONB, nullable=False),
    Column("timetable", JSONB, nullable=False),
)

node_connections_table = Table(
    "node_connections",
    metadata,
    Column("from_id", Uuid, primary_key=True),
    Column("to_id", Uuid, primary_key=True),
)

node_layouts_table = Table(
    "node_layouts",
    metadata,
    Column("node_id", Uuid, primary_key=True),
    Column("x", Float, nullable=False),
    Column("y", Float, nullable=False),
)

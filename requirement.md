# Assignment - Vehicle Scheduling System

## Overview

This assignment is part of our interview process. You are expected to design and implement a **vehicle scheduling system** (frontend + backend) based on the track map defined below.

Your submission will be the basis for discussion during the next interview. We are interested in your design decisions, code quality, and problem-solving approach.

**Deadline: 2 weeks from the date you receive this assignment.**

---

## Table of Contents
[TOC]

---

## Track Map

![image](https://hackmd.io/_uploads/HknXXRyjbl.png)

## Components

| **Component** | **Name(s)** | **Description** |
| --- | --- | --- |
| Yard | Y | Depot where vehicles are stored and charged |
| Stations | S1, S2, S3 | Passenger stations |
| Platforms | P1A, P1B, P2A, P2B, P3A, P3B | Platforms at each station (2 per station) |
| Blocks | B1 – B14 | Track segments connecting the above nodes |

### Rules

* All blocks are **unidirectional** — vehicles may only travel in the direction indicated by the arrows on the map.
* A valid path must follow the connectivity defined in the adjacency list below.

### Interlocking Constraints

The following groups of blocks share an **interlocking** relationship. Within each group, only **one vehicle** may occupy **any** block in the group at a time:

| **Group** | **Blocks** |
| --- | --- |
| 1 | B1, B2 |
| 2 | B3, B4, B13, B14 |
| 3 | B7, B8, B9, B10 |

### Adjacency List

Each entry defines the directed connectivity between nodes and blocks.

**Legend**: `->` one-way connection

```
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
```

---

## Core Requirements

The following features are **mandatory**.

### 1. Service Definition

A **service** represents a single scheduled vehicle run and consists of:

| **Field** | **Description** | **Example** |
| --- | --- | --- |
| Service ID | Numeric identifier | `101`, `102` |
| Vehicle ID | Identifier for the vehicle | `V1`, `V2` |
| Path | Ordered sequence of blocks and platforms the vehicle traverses | `Y → B1 → P1A → …` |
| Times | Arrival and departure time at each platform along the path | — |

### 2. Schedule Management (CRUD)

* Users can **create**, **read**, **update**, and **delete** services.
* When creating or updating a service, the path must consist of **consecutively connected blocks** as defined in the adjacency list. The system must **validate path connectivity**.
* A vehicle may be assigned to multiple services. The system must handle conflicts arising from multiple services assigned to the same vehicle (e.g., overlapping time windows, location discontinuity between consecutive services).

### 3. Pages

The application must include the following pages:

| **Page** | **Type** | **Description** |
| --- | --- | --- |
| **Schedule Editor** | Read/Write | Add, edit, and delete services (path, vehicle, timing) |
| **Schedule Viewer** | Read-only | Display the full schedule in a clear, organized format |
| **Block Configuration** | Read/Write | Configure the **traversal time** for each block (each block may have a different duration) |

### 4. Unit Tests

The backend must include **unit tests**. The scope and coverage are up to you.

## Bonus Requirements

The following features are **optional** and can be completed **independently** — you may choose any subset. Completing bonus requirements will be considered favorably.

### Bonus 1 — Conflict Detection

The system should detect and report the following schedule conflicts:

#### 1.1 Block Occupancy Conflict

A block can only be occupied by **one vehicle at a time**. If two or more vehicles occupy the same block during overlapping time windows, this is a conflict.

> A vehicle occupies a block for the duration of its configured traversal time.

#### 1.2 Low Battery

| **Parameter** | **Value** |
| --- | --- |
| Initial battery | 80 |
| Max capacity | 100 |
| Cost per block | 1 |
| Low battery threshold | 30 |

* A vehicle must return to the **Yard (Y)** before its battery drops below **30**.
* If a vehicle's battery reaches **< 30** and it is not in the Yard → **low battery conflict**.

#### 1.3 Insufficient Charge on Departure

| **Parameter** | **Value** |
| --- | --- |
| Required on departure | >= 80 |
| Charge rate in Yard | 12 seconds/unit |

* If a vehicle departs the Yard with battery below 80 → **insufficient charge conflict**.

### Bonus 2 — Interactive Track Map

Implement an interactive visualization of the track map using **d3.js** or any equivalent library.

* Render the track map as shown in the diagram above.

#### 2.1 Interactive Path Editing

* Users can click on blocks, platforms, and the yard to interactively build a service path.
* The selected path should be visually highlighted on the map.

#### 2.2 Schedule Simulation / Playback

Implement a **simulation mode** that plays back the schedule in accelerated time on the track map. During playback, visualize as much real-time information as possible:

* Vehicle positions on the track
* Active service for each vehicle
* Battery levels
* Any detected conflicts (if Bonus 1 is implemented)

### Bonus 3 — Auto-Generate Schedule

Implement an automatic schedule generation feature.

**Inputs**:

| **Parameter** | **Example** |
| --- | --- |
| Departure interval | Every 5 minutes |
| Time range | 08:00 – 18:00 |

* All generated services must have **no conflicts** (no block occupancy conflicts, no interlocking violations).
* At every station, a passenger waits **at most** the specified interval before a vehicle arrives heading in **any** direction.
* e.g., with a 5-minute interval, a passenger at any station can board a vehicle within 5 minutes, regardless of destination.

## Technical Requirements

| **Layer** | **Technology** |
| --- | --- |
| Frontend | Angular (latest stable) |
| Backend | Python + FastAPI |
| Database | PostgreSQL |
| Containerization | Docker + Docker Compose |

## Submission Guidelines

1. **Repository**: Host your code in a **GitHub repository** (public, or private with access granted to the reviewers).
2. **README**: Your repository must include a `README.md` with:
   * Setup and run instructions
   * Data model design and rationale
   * API design overview
   * At least one design trade-off you considered and why you chose your approach
   * Any assumptions you made
3. **Docker**: The project must include a `Dockerfile` and `docker-compose.yml`. The entire application must be runnable with a single command:

    ```shell
    docker compose up
    ```

4. **Deadline**: Please submit your repository link within **2 weeks** of receiving this assignment.

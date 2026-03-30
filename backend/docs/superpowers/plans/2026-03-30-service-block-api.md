# Service CRUD & Block Read/Update API Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add REST APIs for Service CRUD and Block read/update, backed by in-memory repositories.

**Architecture:** Hexagonal architecture with domain ports, application services, and FastAPI routes. In-memory repositories implement domain ports. FastAPI `Depends()` wires everything together.

**Tech Stack:** Python 3.14, FastAPI, Pydantic v2, pytest + pytest-asyncio, httpx (for API tests)

**Spec:** `docs/superpowers/specs/2026-03-30-service-block-api-design.md`

---

### Task 1: Add `update_traversal_time()` to Block domain model

Block is an aggregate root — entities mutate state (like `Service.update_path()`).
Only value objects (like `TimetableEntry`, `Node`) are immutable.

**Files:**
- Modify: `domain/block/model.py:9-28`
- Test: `tests/domain/test_block.py`

- [ ] **Step 1: Write the failing test**

In `tests/domain/test_block.py`, add to `TestBlock`:

```python
def test_update_traversal_time(self):
    block = Block(id=uuid7(), name="B1", group=1, traversal_time_seconds=30)
    block.update_traversal_time(60)
    assert block.traversal_time_seconds == 60

def test_update_traversal_time_rejects_invalid(self):
    block = Block(id=uuid7(), name="B1", group=1, traversal_time_seconds=30)
    with pytest.raises(ValueError, match="traversal_time_seconds must be positive"):
        block.update_traversal_time(0)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/domain/test_block.py::TestBlock::test_update_traversal_time -v`
Expected: FAIL with `AttributeError: 'Block' object has no attribute 'update_traversal_time'`

- [ ] **Step 3: Write minimal implementation**

In `domain/block/model.py`, add method to `Block` class (after `to_node`):

```python
def update_traversal_time(self, traversal_time_seconds: int) -> None:
    if traversal_time_seconds <= 0:
        raise ValueError("traversal_time_seconds must be positive")
    self.traversal_time_seconds = traversal_time_seconds
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/domain/test_block.py -v`
Expected: All 9 tests PASS

- [ ] **Step 5: Commit**

```bash
git add domain/block/model.py tests/domain/test_block.py
git commit -m "feat: add update_traversal_time to Block model"
```

---

### Task 2: Create unified repository ports

**Files:**
- Create: `domain/service/repository.py`
- Create: `domain/block/repository.py`
- Modify: `domain/service/conflict.py:35-54` (remove old ports, use new repos)
- Modify: `tests/domain/test_conflict.py:37-53` (update fakes)

- [ ] **Step 1: Create ServiceRepository port**

Create `domain/service/repository.py`:

```python
from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from domain.service.model import Service


class ServiceRepository(ABC):
    @abstractmethod
    async def find_all(self) -> list[Service]: ...

    @abstractmethod
    async def find_by_id(self, id: UUID) -> Service | None: ...

    @abstractmethod
    async def find_by_vehicle_id(self, vehicle_id: UUID) -> list[Service]: ...

    @abstractmethod
    async def save(self, service: Service) -> None: ...

    @abstractmethod
    async def delete(self, id: UUID) -> None: ...
```

- [ ] **Step 2: Create BlockRepository port**

Create `domain/block/repository.py`:

```python
from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from domain.block.model import Block


class BlockRepository(ABC):
    @abstractmethod
    async def find_all(self) -> list[Block]: ...

    @abstractmethod
    async def find_by_id(self, id: UUID) -> Block | None: ...

    @abstractmethod
    async def save(self, block: Block) -> None: ...
```

- [ ] **Step 3: Update ConflictDetectionService to use new ports**

In `domain/service/conflict.py`:

1. Remove `ServiceQueryPort` and `BlockQueryPort` classes (lines 35-45)
2. Add imports: `from domain.service.repository import ServiceRepository` and `from domain.block.repository import BlockRepository`
3. Update `ConflictDetectionService.__init__` to accept `ServiceRepository` and `BlockRepository`:

```python
class ConflictDetectionService:
    def __init__(self, service_repo: ServiceRepository, block_repo: BlockRepository) -> None:
        self._service_repo = service_repo
        self._block_repo = block_repo
```

4. Replace `self._service_query` with `self._service_repo` and `self._block_query` with `self._block_repo` throughout the class.

- [ ] **Step 4: Update test fakes to implement new repository interfaces**

In `tests/domain/test_conflict.py`:

1. Replace imports of `ServiceQueryPort`, `BlockQueryPort` with `ServiceRepository`, `BlockRepository`
2. Update `FakeServiceQuery` → `FakeServiceRepo(ServiceRepository)`:

```python
class FakeServiceRepo(ServiceRepository):
    def __init__(self, services: list[Service]):
        self._services = {s.id: s for s in services}

    async def find_by_vehicle_id(self, vehicle_id) -> list[Service]:
        return [s for s in self._services.values() if s.vehicle_id == vehicle_id]

    async def find_all(self) -> list[Service]:
        return list(self._services.values())

    async def find_by_id(self, id) -> Service | None:
        return self._services.get(id)

    async def save(self, service) -> None:
        self._services[service.id] = service

    async def delete(self, id) -> None:
        self._services.pop(id, None)
```

3. Update `FakeBlockQuery` → `FakeBlockRepo(BlockRepository)`:

```python
class FakeBlockRepo(BlockRepository):
    def __init__(self, blocks: list[Block]):
        self._blocks = {b.id: b for b in blocks}

    async def find_all(self) -> list[Block]:
        return list(self._blocks.values())

    async def find_by_id(self, id) -> Block | None:
        return self._blocks.get(id)

    async def save(self, block) -> None:
        self._blocks[block.id] = block
```

4. Update all test usages: `FakeServiceQuery(...)` → `FakeServiceRepo(...)`, `FakeBlockQuery(...)` → `FakeBlockRepo(...)`

- [ ] **Step 5: Run all tests to verify nothing broke**

Run: `uv run pytest tests/ -v`
Expected: All existing tests PASS

- [ ] **Step 6: Commit**

```bash
git add domain/service/repository.py domain/block/repository.py domain/service/conflict.py tests/domain/test_conflict.py
git commit -m "refactor: unify repository ports, replace ServiceQueryPort and BlockQueryPort"
```

---

### Task 3: Create in-memory repositories

**Files:**
- Create: `infra/memory/__init__.py`
- Create: `infra/memory/service_repo.py`
- Create: `infra/memory/block_repo.py`
- Test: `tests/infra/__init__.py`
- Test: `tests/infra/test_memory_service_repo.py`
- Test: `tests/infra/test_memory_block_repo.py`

- [ ] **Step 1: Write failing tests for InMemoryServiceRepository**

Create `tests/infra/__init__.py` (empty file).

Create `tests/infra/test_memory_service_repo.py`:

```python
from uuid import uuid7

import pytest

from domain.network.model import Node, NodeType
from domain.service.model import Service
from infra.memory.service_repo import InMemoryServiceRepository


def make_service(vehicle_id=None) -> Service:
    return Service(
        id=uuid7(),
        name="S1",
        vehicle_id=vehicle_id or uuid7(),
        path=[],
        timetable=[],
    )


class TestInMemoryServiceRepository:
    @pytest.fixture
    def repo(self):
        return InMemoryServiceRepository()

    @pytest.mark.asyncio
    async def test_save_and_find_by_id(self, repo):
        service = make_service()
        await repo.save(service)
        found = await repo.find_by_id(service.id)
        assert found == service

    @pytest.mark.asyncio
    async def test_find_by_id_returns_none(self, repo):
        assert await repo.find_by_id(uuid7()) is None

    @pytest.mark.asyncio
    async def test_find_all(self, repo):
        s1, s2 = make_service(), make_service()
        await repo.save(s1)
        await repo.save(s2)
        result = await repo.find_all()
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_find_by_vehicle_id(self, repo):
        vid = uuid7()
        s1 = make_service(vehicle_id=vid)
        s2 = make_service(vehicle_id=vid)
        s3 = make_service()
        await repo.save(s1)
        await repo.save(s2)
        await repo.save(s3)
        result = await repo.find_by_vehicle_id(vid)
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_delete(self, repo):
        service = make_service()
        await repo.save(service)
        await repo.delete(service.id)
        assert await repo.find_by_id(service.id) is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_is_idempotent(self, repo):
        await repo.delete(uuid7())  # should not raise
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/infra/test_memory_service_repo.py -v`
Expected: FAIL (import error)

- [ ] **Step 3: Implement InMemoryServiceRepository**

Create `infra/memory/__init__.py` (empty file).

Create `infra/memory/service_repo.py`:

```python
from __future__ import annotations

from uuid import UUID

from domain.service.model import Service
from domain.service.repository import ServiceRepository


class InMemoryServiceRepository(ServiceRepository):
    def __init__(self) -> None:
        self._store: dict[UUID, Service] = {}

    async def find_all(self) -> list[Service]:
        return list(self._store.values())

    async def find_by_id(self, id: UUID) -> Service | None:
        return self._store.get(id)

    async def find_by_vehicle_id(self, vehicle_id: UUID) -> list[Service]:
        return [s for s in self._store.values() if s.vehicle_id == vehicle_id]

    async def save(self, service: Service) -> None:
        self._store[service.id] = service

    async def delete(self, id: UUID) -> None:
        self._store.pop(id, None)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/infra/test_memory_service_repo.py -v`
Expected: All 6 tests PASS

- [ ] **Step 5: Write failing tests for InMemoryBlockRepository**

Create `tests/infra/test_memory_block_repo.py`:

```python
from uuid import uuid7

import pytest

from domain.block.model import Block
from infra.memory.block_repo import InMemoryBlockRepository


def make_block() -> Block:
    return Block(id=uuid7(), name="B1", group=1, traversal_time_seconds=30)


class TestInMemoryBlockRepository:
    @pytest.fixture
    def repo(self):
        return InMemoryBlockRepository()

    @pytest.mark.asyncio
    async def test_save_and_find_by_id(self, repo):
        block = make_block()
        await repo.save(block)
        found = await repo.find_by_id(block.id)
        assert found == block

    @pytest.mark.asyncio
    async def test_find_by_id_returns_none(self, repo):
        assert await repo.find_by_id(uuid7()) is None

    @pytest.mark.asyncio
    async def test_find_all(self, repo):
        b1, b2 = make_block(), make_block()
        await repo.save(b1)
        await repo.save(b2)
        result = await repo.find_all()
        assert len(result) == 2
```

- [ ] **Step 6: Implement InMemoryBlockRepository**

Create `infra/memory/block_repo.py`:

```python
from __future__ import annotations

from uuid import UUID

from domain.block.model import Block
from domain.block.repository import BlockRepository


class InMemoryBlockRepository(BlockRepository):
    def __init__(self) -> None:
        self._store: dict[UUID, Block] = {}

    async def find_all(self) -> list[Block]:
        return list(self._store.values())

    async def find_by_id(self, id: UUID) -> Block | None:
        return self._store.get(id)

    async def save(self, block: Block) -> None:
        self._store[block.id] = block
```

- [ ] **Step 7: Run all tests**

Run: `uv run pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 8: Commit**

```bash
git add infra/memory/ tests/infra/
git commit -m "feat: add in-memory repository implementations"
```

---

### Task 4: Create Block application service

**Files:**
- Create: `application/__init__.py` (already exists, empty)
- Create: `application/block/__init__.py`
- Create: `application/block/service.py`
- Test: `tests/application/__init__.py`
- Test: `tests/application/test_block_service.py`

- [ ] **Step 1: Write failing tests**

Create `tests/application/__init__.py` (empty).

Create `tests/application/test_block_service.py`:

```python
from uuid import uuid7

import pytest

from application.block.service import BlockApplicationService
from domain.block.model import Block
from infra.memory.block_repo import InMemoryBlockRepository


class TestBlockApplicationService:
    @pytest.fixture
    def repo(self):
        return InMemoryBlockRepository()

    @pytest.fixture
    def service(self, repo):
        return BlockApplicationService(repo)

    async def _given_block(self, repo, **kwargs) -> Block:
        defaults = dict(id=uuid7(), name="B1", group=1, traversal_time_seconds=30)
        defaults.update(kwargs)
        block = Block(**defaults)
        await repo.save(block)
        return block

    @pytest.mark.asyncio
    async def test_get_block(self, service, repo):
        block = await self._given_block(repo)
        result = await service.get_block(block.id)
        assert result == block

    @pytest.mark.asyncio
    async def test_get_block_not_found(self, service):
        with pytest.raises(ValueError, match="not found"):
            await service.get_block(uuid7())

    @pytest.mark.asyncio
    async def test_list_blocks(self, service, repo):
        await self._given_block(repo)
        await self._given_block(repo)
        result = await service.list_blocks()
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_update_block_traversal_time(self, service, repo):
        block = await self._given_block(repo, traversal_time_seconds=30)
        result = await service.update_block(block.id, traversal_time_seconds=60)
        assert result.traversal_time_seconds == 60
        assert result.id == block.id

    @pytest.mark.asyncio
    async def test_update_block_rejects_invalid_time(self, service, repo):
        block = await self._given_block(repo)
        with pytest.raises(ValueError, match="traversal_time_seconds must be positive"):
            await service.update_block(block.id, traversal_time_seconds=0)

    @pytest.mark.asyncio
    async def test_update_block_not_found(self, service):
        with pytest.raises(ValueError, match="not found"):
            await service.update_block(uuid7(), traversal_time_seconds=60)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/application/test_block_service.py -v`
Expected: FAIL (import error)

- [ ] **Step 3: Implement BlockApplicationService**

Create `application/block/__init__.py` (empty).

Create `application/block/service.py`:

```python
from __future__ import annotations

from uuid import UUID

from domain.block.model import Block
from domain.block.repository import BlockRepository


class BlockApplicationService:
    def __init__(self, block_repo: BlockRepository) -> None:
        self._block_repo = block_repo

    async def get_block(self, id: UUID) -> Block:
        block = await self._block_repo.find_by_id(id)
        if block is None:
            raise ValueError(f"Block {id} not found")
        return block

    async def list_blocks(self) -> list[Block]:
        return await self._block_repo.find_all()

    async def update_block(self, id: UUID, traversal_time_seconds: int) -> Block:
        block = await self._block_repo.find_by_id(id)
        if block is None:
            raise ValueError(f"Block {id} not found")
        block.update_traversal_time(traversal_time_seconds)
        await self._block_repo.save(block)
        return block
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/application/test_block_service.py -v`
Expected: All 6 tests PASS

- [ ] **Step 5: Commit**

```bash
git add application/block/ tests/application/
git commit -m "feat: add BlockApplicationService"
```

---

### Task 5: Create Service application service

**Files:**
- Create: `application/service/__init__.py`
- Create: `application/service/service.py`
- Test: `tests/application/test_service_service.py`

- [ ] **Step 1: Write failing tests**

Create `tests/application/test_service_service.py`:

```python
from uuid import uuid7

import pytest

from application.service.service import ServiceApplicationService
from domain.network.model import Node, NodeType
from domain.service.model import Service, TimetableEntry
from infra.memory.service_repo import InMemoryServiceRepository


class TestServiceApplicationService:
    @pytest.fixture
    def repo(self):
        return InMemoryServiceRepository()

    @pytest.fixture
    def service(self, repo):
        return ServiceApplicationService(repo)

    @pytest.mark.asyncio
    async def test_create_service(self, service):
        vid = uuid7()
        result = await service.create_service(name="Express", vehicle_id=vid)
        assert result.name == "Express"
        assert result.vehicle_id == vid
        assert result.path == []
        assert result.timetable == []

    @pytest.mark.asyncio
    async def test_create_service_rejects_empty_name(self, service):
        with pytest.raises(ValueError, match="name"):
            await service.create_service(name="", vehicle_id=uuid7())

    @pytest.mark.asyncio
    async def test_get_service(self, service, repo):
        created = await service.create_service(name="S1", vehicle_id=uuid7())
        result = await service.get_service(created.id)
        assert result == created

    @pytest.mark.asyncio
    async def test_get_service_not_found(self, service):
        with pytest.raises(ValueError, match="not found"):
            await service.get_service(uuid7())

    @pytest.mark.asyncio
    async def test_list_services(self, service):
        await service.create_service(name="S1", vehicle_id=uuid7())
        await service.create_service(name="S2", vehicle_id=uuid7())
        result = await service.list_services()
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_update_path(self, service):
        created = await service.create_service(name="S1", vehicle_id=uuid7())
        n1 = Node(id=uuid7(), type=NodeType.BLOCK)
        n2 = Node(id=uuid7(), type=NodeType.PLATFORM)
        result = await service.update_service_path(created.id, [n1, n2])
        assert len(result.path) == 2

    @pytest.mark.asyncio
    async def test_update_timetable(self, service):
        created = await service.create_service(name="S1", vehicle_id=uuid7())
        node = Node(id=uuid7(), type=NodeType.BLOCK)
        await service.update_service_path(created.id, [node])
        entries = [TimetableEntry(order=0, node_id=node.id, arrival=0, departure=10)]
        result = await service.update_service_timetable(created.id, entries)
        assert len(result.timetable) == 1

    @pytest.mark.asyncio
    async def test_update_timetable_rejects_unknown_node(self, service):
        created = await service.create_service(name="S1", vehicle_id=uuid7())
        entries = [TimetableEntry(order=0, node_id=uuid7(), arrival=0, departure=10)]
        with pytest.raises(ValueError, match="not in path"):
            await service.update_service_timetable(created.id, entries)

    @pytest.mark.asyncio
    async def test_delete_service(self, service, repo):
        created = await service.create_service(name="S1", vehicle_id=uuid7())
        await service.delete_service(created.id)
        assert await repo.find_by_id(created.id) is None

    @pytest.mark.asyncio
    async def test_delete_service_idempotent(self, service):
        await service.delete_service(uuid7())  # should not raise
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/application/test_service_service.py -v`
Expected: FAIL (import error)

- [ ] **Step 3: Implement ServiceApplicationService**

Create `application/service/__init__.py` (empty).

Create `application/service/service.py`:

```python
from __future__ import annotations

from uuid import UUID, uuid7

from domain.network.model import Node
from domain.service.model import Service, TimetableEntry
from domain.service.repository import ServiceRepository


class ServiceApplicationService:
    def __init__(self, service_repo: ServiceRepository) -> None:
        self._service_repo = service_repo

    async def create_service(self, name: str, vehicle_id: UUID) -> Service:
        if not name or not name.strip():
            raise ValueError("Service name must not be empty")
        service = Service(
            id=uuid7(),
            name=name,
            vehicle_id=vehicle_id,
            path=[],
            timetable=[],
        )
        await self._service_repo.save(service)
        return service

    async def get_service(self, id: UUID) -> Service:
        service = await self._service_repo.find_by_id(id)
        if service is None:
            raise ValueError(f"Service {id} not found")
        return service

    async def list_services(self) -> list[Service]:
        return await self._service_repo.find_all()

    async def update_service_path(self, id: UUID, path: list[Node]) -> Service:
        service = await self.get_service(id)
        service.update_path(path)
        await self._service_repo.save(service)
        return service

    async def update_service_timetable(
        self, id: UUID, timetable: list[TimetableEntry]
    ) -> Service:
        service = await self.get_service(id)
        service.update_timetable(timetable)
        await self._service_repo.save(service)
        return service

    async def delete_service(self, id: UUID) -> None:
        await self._service_repo.delete(id)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/application/test_service_service.py -v`
Expected: All 10 tests PASS

- [ ] **Step 5: Commit**

```bash
git add application/service/ tests/application/test_service_service.py
git commit -m "feat: add ServiceApplicationService"
```

---

### Task 6: Create Block API schemas and routes

**Files:**
- Create: `api/block/__init__.py`
- Create: `api/block/schemas.py`
- Create: `api/block/routes.py`
- Test: `tests/api/__init__.py`
- Test: `tests/api/test_block_routes.py`

**Prerequisite:** Install `httpx` for FastAPI test client: add `"httpx>=0.28.0"` to `[dependency-groups] dev` in `pyproject.toml`.

- [ ] **Step 1: Add httpx dev dependency**

In `pyproject.toml`, add `"httpx>=0.28.0"` to the dev dependency group:

```toml
[dependency-groups]
dev = [
    "pytest>=9.0.2",
    "pytest-asyncio>=1.3.0",
    "httpx>=0.28.0",
]
```

Run: `uv sync`

- [ ] **Step 2: Create Block schemas**

Create `api/block/__init__.py` (empty).

Create `api/block/schemas.py`:

```python
from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field

from domain.block.model import Block


class UpdateBlockRequest(BaseModel):
    traversal_time_seconds: int = Field(gt=0)


class BlockResponse(BaseModel):
    id: UUID
    name: str
    group: int
    traversal_time_seconds: int

    @classmethod
    def from_domain(cls, block: Block) -> BlockResponse:
        return cls(
            id=block.id,
            name=block.name,
            group=block.group,
            traversal_time_seconds=block.traversal_time_seconds,
        )
```

- [ ] **Step 3: Write failing tests for Block routes**

Create `tests/api/__init__.py` (empty).

Create `tests/api/test_block_routes.py`:

```python
from uuid import uuid7

import pytest
from fastapi.testclient import TestClient

from domain.block.model import Block
from infra.memory.block_repo import InMemoryBlockRepository
from main import create_app


@pytest.fixture
def block_repo():
    return InMemoryBlockRepository()


@pytest.fixture
def app(block_repo):
    return create_app(block_repo=block_repo)


@pytest.fixture
def client(app):
    return TestClient(app)


async def seed_block(repo, **kwargs) -> Block:
    defaults = dict(id=uuid7(), name="B1", group=1, traversal_time_seconds=30)
    defaults.update(kwargs)
    block = Block(**defaults)
    await repo.save(block)
    return block


class TestBlockRoutes:
    def test_list_blocks_empty(self, client):
        resp = client.get("/blocks")
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.asyncio
    async def test_list_blocks(self, client, block_repo):
        await seed_block(block_repo)
        await seed_block(block_repo, name="B2")
        resp = client.get("/blocks")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    @pytest.mark.asyncio
    async def test_get_block(self, client, block_repo):
        block = await seed_block(block_repo)
        resp = client.get(f"/blocks/{block.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == str(block.id)
        assert data["traversal_time_seconds"] == 30

    def test_get_block_not_found(self, client):
        resp = client.get(f"/blocks/{uuid7()}")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_update_block(self, client, block_repo):
        block = await seed_block(block_repo)
        resp = client.patch(f"/blocks/{block.id}", json={"traversal_time_seconds": 60})
        assert resp.status_code == 200
        assert resp.json()["traversal_time_seconds"] == 60

    @pytest.mark.asyncio
    async def test_update_block_invalid_time(self, client, block_repo):
        block = await seed_block(block_repo)
        resp = client.patch(f"/blocks/{block.id}", json={"traversal_time_seconds": 0})
        assert resp.status_code == 422

    def test_update_block_not_found(self, client):
        resp = client.patch(f"/blocks/{uuid7()}", json={"traversal_time_seconds": 60})
        assert resp.status_code == 404
```

- [ ] **Step 4: Run tests to verify they fail**

Run: `uv run pytest tests/api/test_block_routes.py -v`
Expected: FAIL (import errors)

- [ ] **Step 5: Create Block routes**

Create `api/block/routes.py`:

```python
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException

from api.block.schemas import BlockResponse, UpdateBlockRequest
from application.block.service import BlockApplicationService


def create_block_router(block_service: BlockApplicationService) -> APIRouter:
    router = APIRouter(prefix="/blocks", tags=["blocks"])

    @router.get("", response_model=list[BlockResponse])
    async def list_blocks():
        blocks = await block_service.list_blocks()
        return [BlockResponse.from_domain(b) for b in blocks]

    @router.get("/{block_id}", response_model=BlockResponse)
    async def get_block(block_id: UUID):
        try:
            block = await block_service.get_block(block_id)
        except ValueError:
            raise HTTPException(status_code=404, detail=f"Block {block_id} not found")
        return BlockResponse.from_domain(block)

    @router.patch("/{block_id}", response_model=BlockResponse)
    async def update_block(block_id: UUID, request: UpdateBlockRequest):
        try:
            block = await block_service.update_block(
                block_id, traversal_time_seconds=request.traversal_time_seconds
            )
        except ValueError as e:
            if "not found" in str(e):
                raise HTTPException(status_code=404, detail=str(e))
            raise HTTPException(status_code=400, detail=str(e))
        return BlockResponse.from_domain(block)

    return router
```

- [ ] **Step 6: Update main.py with create_app factory**

Replace `main.py` content:

```python
from fastapi import FastAPI

from api.block.routes import create_block_router
from application.block.service import BlockApplicationService
from domain.block.repository import BlockRepository
from infra.memory.block_repo import InMemoryBlockRepository


def create_app(
    block_repo: BlockRepository | None = None,
) -> FastAPI:
    app = FastAPI()

    if block_repo is None:
        block_repo = InMemoryBlockRepository()

    block_service = BlockApplicationService(block_repo)
    app.include_router(create_block_router(block_service))

    return app


app = create_app()
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `uv run pytest tests/api/test_block_routes.py -v`
Expected: All 7 tests PASS

- [ ] **Step 8: Commit**

```bash
git add api/block/ tests/api/ main.py pyproject.toml
git commit -m "feat: add Block API endpoints (GET, PATCH)"
```

---

### Task 7: Create Service API schemas and routes

**Files:**
- Create: `api/service/__init__.py`
- Create: `api/service/schemas.py`
- Create: `api/service/routes.py`
- Modify: `main.py` (add service router)
- Test: `tests/api/test_service_routes.py`

- [ ] **Step 1: Create Service schemas**

Create `api/service/__init__.py` (empty).

Create `api/service/schemas.py`:

```python
from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from domain.service.model import Service


class CreateServiceRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    vehicle_id: UUID


class NodeSchema(BaseModel):
    id: UUID
    type: Literal["block", "platform"]


class UpdatePathRequest(BaseModel):
    path: list[NodeSchema]


class TimetableEntrySchema(BaseModel):
    order: int
    node_id: UUID
    arrival: int
    departure: int


class UpdateTimetableRequest(BaseModel):
    timetable: list[TimetableEntrySchema]


class ServiceResponse(BaseModel):
    id: UUID
    name: str
    vehicle_id: UUID
    path: list[NodeSchema]
    timetable: list[TimetableEntrySchema]

    @classmethod
    def from_domain(cls, service: Service) -> ServiceResponse:
        return cls(
            id=service.id,
            name=service.name,
            vehicle_id=service.vehicle_id,
            path=[NodeSchema(id=n.id, type=n.type.value) for n in service.path],
            timetable=[
                TimetableEntrySchema(
                    order=e.order,
                    node_id=e.node_id,
                    arrival=e.arrival,
                    departure=e.departure,
                )
                for e in service.timetable
            ],
        )
```

- [ ] **Step 2: Write failing tests for Service routes**

Create `tests/api/test_service_routes.py`:

```python
from uuid import uuid7

import pytest
from fastapi.testclient import TestClient

from infra.memory.block_repo import InMemoryBlockRepository
from infra.memory.service_repo import InMemoryServiceRepository
from main import create_app


@pytest.fixture
def service_repo():
    return InMemoryServiceRepository()


@pytest.fixture
def app(service_repo):
    return create_app(service_repo=service_repo)


@pytest.fixture
def client(app):
    return TestClient(app)


class TestServiceCRUD:
    def test_create_service(self, client):
        vid = str(uuid7())
        resp = client.post("/services", json={"name": "Express", "vehicle_id": vid})
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Express"
        assert data["vehicle_id"] == vid
        assert data["path"] == []
        assert data["timetable"] == []

    def test_create_service_empty_name_rejected(self, client):
        resp = client.post("/services", json={"name": "", "vehicle_id": str(uuid7())})
        assert resp.status_code == 422

    def test_list_services_empty(self, client):
        resp = client.get("/services")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_services(self, client):
        client.post("/services", json={"name": "S1", "vehicle_id": str(uuid7())})
        client.post("/services", json={"name": "S2", "vehicle_id": str(uuid7())})
        resp = client.get("/services")
        assert len(resp.json()) == 2

    def test_get_service(self, client):
        create_resp = client.post(
            "/services", json={"name": "S1", "vehicle_id": str(uuid7())}
        )
        sid = create_resp.json()["id"]
        resp = client.get(f"/services/{sid}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "S1"

    def test_get_service_not_found(self, client):
        resp = client.get(f"/services/{uuid7()}")
        assert resp.status_code == 404

    def test_delete_service(self, client):
        create_resp = client.post(
            "/services", json={"name": "S1", "vehicle_id": str(uuid7())}
        )
        sid = create_resp.json()["id"]
        resp = client.delete(f"/services/{sid}")
        assert resp.status_code == 204
        assert client.get(f"/services/{sid}").status_code == 404

    def test_delete_service_idempotent(self, client):
        resp = client.delete(f"/services/{uuid7()}")
        assert resp.status_code == 204


class TestServicePathUpdate:
    def test_update_path(self, client):
        create_resp = client.post(
            "/services", json={"name": "S1", "vehicle_id": str(uuid7())}
        )
        sid = create_resp.json()["id"]
        nid = str(uuid7())
        resp = client.patch(
            f"/services/{sid}/path",
            json={"path": [{"id": nid, "type": "block"}]},
        )
        assert resp.status_code == 200
        assert len(resp.json()["path"]) == 1

    def test_update_path_not_found(self, client):
        resp = client.patch(
            f"/services/{uuid7()}/path",
            json={"path": []},
        )
        assert resp.status_code == 404


class TestServiceTimetableUpdate:
    def test_update_timetable(self, client):
        create_resp = client.post(
            "/services", json={"name": "S1", "vehicle_id": str(uuid7())}
        )
        sid = create_resp.json()["id"]
        nid = str(uuid7())
        client.patch(
            f"/services/{sid}/path",
            json={"path": [{"id": nid, "type": "block"}]},
        )
        resp = client.patch(
            f"/services/{sid}/timetable",
            json={
                "timetable": [
                    {"order": 0, "node_id": nid, "arrival": 0, "departure": 10}
                ]
            },
        )
        assert resp.status_code == 200
        assert len(resp.json()["timetable"]) == 1

    def test_update_timetable_node_not_in_path(self, client):
        create_resp = client.post(
            "/services", json={"name": "S1", "vehicle_id": str(uuid7())}
        )
        sid = create_resp.json()["id"]
        resp = client.patch(
            f"/services/{sid}/timetable",
            json={
                "timetable": [
                    {"order": 0, "node_id": str(uuid7()), "arrival": 0, "departure": 10}
                ]
            },
        )
        assert resp.status_code == 400

    def test_update_timetable_not_found(self, client):
        resp = client.patch(
            f"/services/{uuid7()}/timetable",
            json={"timetable": []},
        )
        assert resp.status_code == 404
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `uv run pytest tests/api/test_service_routes.py -v`
Expected: FAIL (import errors)

- [ ] **Step 4: Create Service routes**

Create `api/service/routes.py`:

```python
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException
from starlette.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT

from api.service.schemas import (
    CreateServiceRequest,
    ServiceResponse,
    UpdatePathRequest,
    UpdateTimetableRequest,
)
from application.service.service import ServiceApplicationService
from domain.network.model import Node, NodeType
from domain.service.model import TimetableEntry


def create_service_router(service_service: ServiceApplicationService) -> APIRouter:
    router = APIRouter(prefix="/services", tags=["services"])

    @router.post("", response_model=ServiceResponse, status_code=HTTP_201_CREATED)
    async def create_service(request: CreateServiceRequest):
        try:
            service = await service_service.create_service(
                name=request.name, vehicle_id=request.vehicle_id
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        return ServiceResponse.from_domain(service)

    @router.get("", response_model=list[ServiceResponse])
    async def list_services():
        services = await service_service.list_services()
        return [ServiceResponse.from_domain(s) for s in services]

    @router.get("/{service_id}", response_model=ServiceResponse)
    async def get_service(service_id: UUID):
        try:
            service = await service_service.get_service(service_id)
        except ValueError:
            raise HTTPException(status_code=404, detail=f"Service {service_id} not found")
        return ServiceResponse.from_domain(service)

    @router.patch("/{service_id}/path", response_model=ServiceResponse)
    async def update_path(service_id: UUID, request: UpdatePathRequest):
        path = [
            Node(id=n.id, type=NodeType(n.type)) for n in request.path
        ]
        try:
            service = await service_service.update_service_path(service_id, path)
        except ValueError as e:
            if "not found" in str(e):
                raise HTTPException(status_code=404, detail=str(e))
            raise HTTPException(status_code=400, detail=str(e))
        return ServiceResponse.from_domain(service)

    @router.patch("/{service_id}/timetable", response_model=ServiceResponse)
    async def update_timetable(service_id: UUID, request: UpdateTimetableRequest):
        entries = [
            TimetableEntry(
                order=e.order,
                node_id=e.node_id,
                arrival=e.arrival,
                departure=e.departure,
            )
            for e in request.timetable
        ]
        try:
            service = await service_service.update_service_timetable(service_id, entries)
        except ValueError as e:
            if "not found" in str(e):
                raise HTTPException(status_code=404, detail=str(e))
            raise HTTPException(status_code=400, detail=str(e))
        return ServiceResponse.from_domain(service)

    @router.delete("/{service_id}", status_code=HTTP_204_NO_CONTENT)
    async def delete_service(service_id: UUID):
        await service_service.delete_service(service_id)

    return router
```

- [ ] **Step 5: Update main.py to include service router**

Replace `main.py` content:

```python
from fastapi import FastAPI

from api.block.routes import create_block_router
from api.service.routes import create_service_router
from application.block.service import BlockApplicationService
from application.service.service import ServiceApplicationService
from domain.block.repository import BlockRepository
from domain.service.repository import ServiceRepository
from infra.memory.block_repo import InMemoryBlockRepository
from infra.memory.service_repo import InMemoryServiceRepository


def create_app(
    block_repo: BlockRepository | None = None,
    service_repo: ServiceRepository | None = None,
) -> FastAPI:
    app = FastAPI()

    if block_repo is None:
        block_repo = InMemoryBlockRepository()
    if service_repo is None:
        service_repo = InMemoryServiceRepository()

    block_service = BlockApplicationService(block_repo)
    app.include_router(create_block_router(block_service))

    service_service = ServiceApplicationService(service_repo)
    app.include_router(create_service_router(service_service))

    return app


app = create_app()
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `uv run pytest tests/api/test_service_routes.py -v`
Expected: All 11 tests PASS

- [ ] **Step 7: Run full test suite**

Run: `uv run pytest tests/ -v`
Expected: ALL tests PASS

- [ ] **Step 8: Commit**

```bash
git add api/service/ tests/api/test_service_routes.py main.py
git commit -m "feat: add Service API endpoints (CRUD + path/timetable update)"
```

---

### Task 8: Final verification

- [ ] **Step 1: Run full test suite**

Run: `uv run pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 2: Start the server and smoke test**

Run: `uv run uvicorn main:app --reload`

Verify in browser: `http://localhost:8000/docs` — should show all endpoints in OpenAPI docs.

- [ ] **Step 3: Commit any remaining changes**

If no changes needed, skip this step.

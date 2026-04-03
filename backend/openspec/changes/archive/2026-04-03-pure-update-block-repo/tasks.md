## 1. Postgres Repository

- [x] 1.1 Replace upsert with pure `UPDATE` in `PostgresBlockRepository.update()` and raise `ValueError` when no rows affected

## 2. In-Memory Fake

- [x] 2.1 Add `ValueError` guard to `InMemoryBlockRepository.update()` when block ID not in store

## 3. Tests

- [x] 3.1 Update `test_postgres_block_repo.py`: replace `repo.update()` seed calls with direct SQL inserts, add test for updating non-existent block raises `ValueError`
- [x] 3.2 Add unit test for `InMemoryBlockRepository` raising `ValueError` on non-existent block update

## Why

`PostgresBlockRepository.update()` uses upsert (`INSERT ... ON CONFLICT DO UPDATE`), but blocks are seed data that always exist in the database. The method is only called to modify existing blocks (e.g., updating traversal time). Using upsert here is semantically misleading and masks potential bugs -- if a non-existent block ID were passed, the upsert would silently insert a new row instead of failing.

## What Changes

- Replace the upsert (`insert().on_conflict_do_update()`) in `PostgresBlockRepository.update()` with a pure SQL `UPDATE` statement
- Update the integration test to verify update-only semantics (no silent insert)
- Update the in-memory fake to match: raise on update of non-existent block

## Capabilities

### New Capabilities

- `pure-update-block`: Replace upsert with pure UPDATE in block repository, ensuring update-only semantics

### Modified Capabilities

## Impact

- `infra/postgres/block_repo.py` -- change `update()` implementation
- `tests/fakes/block_repo.py` -- align fake with update-only contract
- `tests/infra/test_postgres_block_repo.py` -- update tests for new semantics

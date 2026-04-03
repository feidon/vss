## Context

`PostgresBlockRepository.update()` currently uses `INSERT ... ON CONFLICT DO UPDATE` (upsert). Blocks are infrastructure seed data loaded via Alembic migrations -- they are never created through the application. The only mutation is updating `traversal_time_seconds` on an existing block.

## Goals / Non-Goals

**Goals:**
- Replace upsert with a pure `UPDATE` statement so the method has correct semantics
- Ensure attempting to update a non-existent block is surfaced as an error rather than silently inserting

**Non-Goals:**
- Adding a `save()` or `create()` method -- block creation remains in seed data only
- Changing the repository interface signature or return type

## Decisions

1. **Use SQLAlchemy Core `update()` instead of `insert().on_conflict_do_update()`**
   - Rationale: The method is named `update` and is only ever called with existing block IDs. A pure UPDATE matches the intent. An upsert silently masks bugs where a non-existent ID is passed.
   - Alternative: Keep upsert but add a precondition check -- rejected because it adds a query and the upsert is still semantically wrong.

2. **Raise `ValueError` if no rows affected**
   - Rationale: Zero rows updated means the block ID doesn't exist. This is always a programming error in the current domain (blocks come from seed data). Failing fast surfaces the bug immediately.
   - Alternative: Return silently -- rejected because it hides bugs.

3. **Align in-memory fake with the same contract**
   - Rationale: Fakes must honour the same contract as the real implementation. The in-memory repo should raise `ValueError` if the block doesn't exist.

## Risks / Trade-offs

- [Risk] Existing tests use `update()` to seed blocks into the database for test setup → Tests must be updated to use direct SQL inserts or a separate seed helper for initial block creation.
- [Risk] If any production code path ever calls `update()` on a non-existent block, it will now fail → This is the intended behavior; it surfaces bugs rather than hiding them.

## ADDED Requirements

### Requirement: Seed fixed track network into PostgreSQL
The system SHALL provide an async `seed_database(session)` function that inserts the complete track network (stations, platforms, blocks, vehicles, node connections) into PostgreSQL. It SHALL reuse the existing data definitions from `infra/seed.py`.

#### Scenario: Seed empty database
- **WHEN** `seed_database(session)` is called and all tables are empty
- **THEN** all 4 stations, 6 platforms, 14 blocks, 3 vehicles, and all node connections are inserted

#### Scenario: Seed already-populated database
- **WHEN** `seed_database(session)` is called and tables already contain data
- **THEN** no duplicate rows are inserted (idempotent via ON CONFLICT DO NOTHING or pre-check)

### Requirement: Seed runs on application startup in postgres mode
The system SHALL execute database seeding on application startup when `DB=postgres` is configured, before the first request is served.

#### Scenario: Startup with empty database
- **WHEN** the application starts with `DB=postgres` and the database has no seed data
- **THEN** the track network is seeded before any API request is handled

#### Scenario: Startup with existing data
- **WHEN** the application starts with `DB=postgres` and seed data already exists
- **THEN** no error occurs and no data is duplicated

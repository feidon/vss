## MODIFIED Requirements

### Requirement: Seed runs on application startup in postgres mode
The system SHALL execute database seeding on application startup unconditionally (no `DB` environment variable check), before the first request is served. Since production always uses PostgreSQL, the lifespan SHALL always initialize the database schema and run seed data.

#### Scenario: Startup with empty database
- **WHEN** the application starts and the database has no seed data
- **THEN** the schema is created and the track network is seeded before any API request is handled

#### Scenario: Startup with existing data
- **WHEN** the application starts and seed data already exists
- **THEN** no error occurs and no data is duplicated

#### Scenario: No conditional DB check in lifespan
- **WHEN** `main.py` source code is inspected
- **THEN** the lifespan function does not check `os.getenv("DB")` — database initialization runs unconditionally

## ADDED Requirements

### Requirement: Track adjacency list in project documentation
CLAUDE.md and openspec/config.yaml SHALL include the complete track adjacency list with direction notation showing all 14 blocks, their connections, and directionality (B1/B2 bidirectional, all others unidirectional).

#### Scenario: CLAUDE.md contains adjacency list
- **WHEN** a contributor reads the Track Network section of CLAUDE.md
- **THEN** the full adjacency list is present with `->` and `<-` notation matching `infra/seed.py`

#### Scenario: openspec config contains adjacency list
- **WHEN** an OpenSpec change references the project context
- **THEN** the Track Network section includes the adjacency list and direction semantics

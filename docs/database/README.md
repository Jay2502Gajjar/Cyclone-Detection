# Database documentation

The schema is defined by Flyway migrations, which are the single source of truth:

- `backend/src/main/resources/db/migration/V1__schema.sql` — the eight tables
- `V2__indexes.sql` — indexes for the two hot paths
- `V3__seed_registry.sql` — the Phase 0 model registry

The design rationale, the entity relationships and the IBTrACS/HURSAT join are in
[`docs/architecture.md`](../architecture.md).

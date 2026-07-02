# Releases and tags

Git tags mark **merge milestones** in this repo. They make it easy to check out exactly what shipped after a phase PR lands.

## Tag types

| Prefix | When to create | Example |
| --- | --- | --- |
| `phase-N` | After a **implementation phase** PR merges to `main` | `phase-3` |
| `vX.Y.Z` | When a **product version** from [SPECS.md §17](../SPECS.md#17-mvp-roadmap) is fully shipped | `v0.1.0` (not yet) |

**Phase tags** track development milestones (Phase 0–12 in [CURSOR_ROADMAP.md](CURSOR_ROADMAP.md)).

**Version tags** track user-facing releases. v0.1 is not complete until Phase 4 (frontend shell) and remaining v0.1 scope land — do not tag `v0.1.0` after backend-only phases.

## Workflow (after merging a phase PR)

1. Update [BACKLOG.md](BACKLOG.md) — mark the phase done, note merge commit and PR number.
2. Create an **annotated** tag on the **merge commit** (not a later docs-only commit):

```bash
git fetch origin main
git tag -a phase-3 -m "Phase 3: Core catalog data (PR #2)" 815d67b
git push origin phase-3
```

3. Add a row to the table below.

## Tagged milestones

| Tag | Commit | Date | Notes |
| --- | --- | --- | --- |
| `phase-3` | `815d67b` | 2026-07-02 | Core catalog data — dishes, recipes, ingredients, YAML seed, quantities service (PR #2) |

Phases 0–2 were merged before this tagging convention existed; tags were not applied retroactively.

## Check out a milestone

```bash
git checkout phase-3
docker compose up --build
```

Run migrations and seed as usual (`make up` on the API applies both).

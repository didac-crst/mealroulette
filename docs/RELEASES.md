# Releases and tags

Git tags mark milestones in this repo. **Phase tags are development checkpoints**, not product releases.

## Tag types

| Tag | When | User-facing? | Example |
| --- | --- | --- | --- |
| `phase-N` | After an implementation phase PR merges | No — engineers only | `phase-3` |
| `vX.Y.Z` | When a **product version** is fully shipped | Yes | `v0.1.0` (after Phase 4) |

### Phase tags (`phase-N`)

Use after each phase in [CURSOR_ROADMAP.md](CURSOR_ROADMAP.md) merges to `main`. Good for:

- Checking out a known-good milestone
- Comparing what changed between phases
- CI or docs references

**Not** a semver release. Do not treat `phase-3` as “MealRoulette v0.1”.

### Version tags (`vX.Y.Z`)

Use only when a row in the [product roadmap](BACKLOG.md#product-roadmap-long-term) is complete.

| Version | Tag when | Current state |
| --- | --- | --- |
| v0.1 Foundation | Phase 4 merges (login + dish library UI) | **Not ready** — backend catalog done, UI pending |
| v0.2+ | Respective version scope complete | Not started |

## Workflow (after merging a phase PR)

1. Update [BACKLOG.md](BACKLOG.md) — mark the phase done, note merge commit and PR number.
2. Create an **annotated** tag on the **merge commit**:

```bash
git fetch origin main
git tag -a phase-3 -m "Phase 3: Core catalog data (PR #2)" 815d67b
git push origin phase-3
```

3. Add a row to the table below.
4. If that was the **last phase** for a product version, also tag `vX.Y.Z` on the same merge commit and update the roadmap status.

## Tagged milestones

| Tag | Commit | Date | What shipped |
| --- | --- | --- | --- |
| `phase-3` | `815d67b` | 2026-07-02 | **Backend catalog** — dishes, recipes, ingredients, units, tags, YAML reference seed, quantity aggregation rules, catalog APIs (PR #2). Frontend dish UI not included. |

Phases 0–2 merged before this convention; no retroactive tags.

## Check out a milestone

```bash
git checkout phase-3
docker compose up --build
```

Run migrations and seed as usual (`make up` on the API applies both).

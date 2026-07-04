# Releases and tags

Git tags mark **product versions** users can run. We do not tag individual implementation phases — only completed versions from the [product roadmap](BACKLOG.md#product-roadmap-long-term).

## When to tag

| Tag | When |
| --- | --- |
| `v0.1.0` | Phase 4 merged — foundation complete (platform, auth, catalog API + dish UI) — **released** |
| `v0.2.0` | Phase 5 merged — manual meal planning (plan/review, actions, ratings, lightweight leftovers) — **released** |
| `v0.3.0` | Phase 6 merged — shopping lists, ingredient catalog, unit aggregation — **released** |
| `v0.4.0` | Phase 7 merged — Telegram reminders, bot commands, recipe links — **released** |
| `v0.5.0` | Phase 8 merged — explainable scheduler, family-vector similarity, scheduled roulette — *(ready, PR #8)* — [release notes](releases/v0.5.0.md) |

Use [semantic versioning](https://semver.org/) at the product-version level: `vMAJOR.MINOR.PATCH`. Patch bumps are for fixes on an already-released version line.

## Workflow (after a product version is complete)

Example: when Phase 4 merges and v0.1 is done:

1. Update [BACKLOG.md](BACKLOG.md) — set the version row to **Done**, note merge commit and PR.
2. Create an **annotated** tag on the **merge commit**:

```bash
git fetch origin main
git tag -a v0.1.0 -m "v0.1 Foundation: platform, auth, catalog API, dish library UI" <merge-commit>
git push origin v0.1.0
```

3. Add a row to the table below.

## Tagged releases

| Tag | Commit | Date | What shipped |
| --- | --- | --- | --- |
| [`v0.1.0`](https://github.com/didac-crst/mealroulette/releases/tag/v0.1.0) | [`b41cdae`](https://github.com/didac-crst/mealroulette/commit/b41cdae) | 2026-07-02 | Foundation: platform, auth, catalog API, dish library UI — [release notes](releases/v0.1.0.md) |
| [`v0.2.0`](https://github.com/didac-crst/mealroulette/releases/tag/v0.2.0) | [`fb20858`](https://github.com/didac-crst/mealroulette/commit/fb20858) | 2026-07-03 | Manual planning: weekly plan, review flow, meal actions, ratings, lightweight leftovers — [release notes](releases/v0.2.0.md) |
| [`v0.3.0`](https://github.com/didac-crst/mealroulette/releases/tag/v0.3.0) | [`88d2675`](https://github.com/didac-crst/mealroulette/commit/88d2675) | 2026-07-03 | Shopping lists, ingredient catalog, unit aggregation — [release notes](releases/v0.3.0.md) |
| [`v0.4.0`](https://github.com/didac-crst/mealroulette/releases/tag/v0.4.0) | [`a560e7a`](https://github.com/didac-crst/mealroulette/commit/a560e7a) | 2026-07-04 | Telegram reminders, bot commands, recipe links — [release notes](releases/v0.4.0.md) |

## Check out a release

```bash
git checkout v0.4.0   # latest tagged release
docker compose up --build
```

Until the first release tag exists, use the merge commit hash or `main`.

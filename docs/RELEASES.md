# Releases and tags

Git tags mark **product versions** users can run. We do not tag individual implementation phases — only completed versions from the [product roadmap](BACKLOG.md#product-roadmap-long-term).

## When to tag

| Tag | When |
| --- | --- |
| `v0.1.0` | Phase 4 merges — foundation complete (platform, auth, catalog API + dish UI) |
| `v0.2.0`, … | Each subsequent product version when its roadmap scope is fully shipped |

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
| *(none yet)* | — | — | First tag will be `v0.1.0` after Phase 4 |

## Check out a release

```bash
git checkout v0.1.0   # once tagged
docker compose up --build
```

Until the first release tag exists, use the merge commit hash or `main`.

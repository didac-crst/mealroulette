# Documentation map

Where to look for product truth, feature behaviour, operations, and history.

## Document metadata

- **Purpose:** Authority map for all repository documentation.
- **Authority:** Canonical index; defers to linked documents for detail.
- **Status:** Living — update when docs move or new feature specs are added.
- **Update when:** A new feature spec, ADR, or operations runbook is added; or folder layout changes.

## Naming convention

| Location | Filename pattern | Title (H1) |
| --- | --- | --- |
| Repo root | `UPPERCASE.md` for conventional docs | Product name or role |
| `docs/` control docs | `BACKLOG.md`, `CURSOR_ROADMAP.md`, `MVP.md` | Descriptive title |
| `docs/features/`, `docs/operations/`, `docs/archive/` | `lowercase-kebab-case.md` | Title Case, no phase labels |
| `docs/adr/` | `NNN-short-kebab-title.md` | `ADR NNN — …` |
| `docs/releases/` | `vX.Y.Z.md` | `vX.Y.Z — …` |
| `docs/taxonomy/` | snake_case for working artifacts | Mark proposal/report/log in metadata |

---

## Product truth

| Document | Role |
| --- | --- |
| [SPECS.md](../SPECS.md) | Long-term product requirements, data model overview, API surface |
| [MVP.md](MVP.md) | MVP goal and acceptance test only — scope detail lives in SPECS |
| [BACKLOG.md](BACKLOG.md) | **Status board** — current focus, phase/version shipment, known debt |
| [CURSOR_ROADMAP.md](CURSOR_ROADMAP.md) | **Build sequence** — phase deliverables and acceptance criteria (not live status) |

## Strategy / operating assumptions

These documents capture dated business and operating assumptions that may drive later technical decisions. They are not release promises.

| Document | Topic |
| --- | --- |
| [strategy/ai-cost-and-credits.md](strategy/ai-cost-and-credits.md) | AI cost order-of-magnitude, credits, managed-vs-BYO provider strategy |
| [strategy/hosting-and-public-beta.md](strategy/hosting-and-public-beta.md) | Hosting cost assumptions, beta staging, operational thresholds |
| [strategy/public-beta-readiness.md](strategy/public-beta-readiness.md) | Go/no-go criteria, success metrics, risk register, public beta gates |
| [strategy/public-catalog-contribution-and-rewards.md](strategy/public-catalog-contribution-and-rewards.md) | Public recipe contribution incentives, reputation, rewards, anti-fraud |
| [strategy/mobile-app-strategy.md](strategy/mobile-app-strategy.md) | Mobile-first web, PWA, Capacitor, and future native-client strategy |

## Feature behaviour (approved semantics)

| Document | Topic |
| --- | --- |
| [features/backup-export-import.md](features/backup-export-import.md) | JSON export/import format, backup settings, validation |
| [features/taxonomy-resolver.md](features/taxonomy-resolver.md) | Ingredient taxonomy, resolver, food groups and families |
| [features/computed-traits.md](features/computed-traits.md) | Recipe computed traits and catalog keys |
| [features/scheduler.md](features/scheduler.md) | Family vectors, similarity, weekly targets |
| [features/pair-compatibility-reroll.md](features/pair-compatibility-reroll.md) | Composable-meal pair scoring and reroll memory |
| [features/cooking-mode.md](features/cooking-mode.md) | Today home, step-by-step cooking, timers |
| [features/meal-outcomes-leftovers.md](features/meal-outcomes-leftovers.md) | Meal outcome review, leftover batches, use-soon hints, planning/shopping integration |
| [features/meal-composition.md](features/meal-composition.md) | Dish `meal_composition` / planner slots |
| [features/composable-meals.md](features/composable-meals.md) | Multi-dish meal slots, do-not-plan, composable roulette |
| [features/ingredient-proposals.md](features/ingredient-proposals.md) | Governed missing-ingredient proposal workflow |
| [features/public-catalog.md](features/public-catalog.md) | Authenticated public recipe catalog, snapshots, adoption |
| [features/recipe-import-drafts.md](features/recipe-import-drafts.md) | Draft-first recipe import and AI-assisted authoring architecture |
| [features/ai-usage-accounting.md](features/ai-usage-accounting.md) | Managed AI usage events, credit ledger, budgets, BYO provider mode |
| [features/email-delivery.md](features/email-delivery.md) | Transactional email provider abstraction, OTP policy, deliverability |
| [features/localization.md](features/localization.md) | Multilingual content design (not yet implemented) |
| [features/ui-ux-design-system.md](features/ui-ux-design-system.md) | Visual design system, tokens, navigation, migration plan |

Implementation detail for taxonomy YAML and validation workflows: [taxonomy/README.md](taxonomy/README.md).

## Architecture decisions (durable)

| ADR | Decision |
| --- | --- |
| [adr/001-ingredient-taxonomy-contract.md](adr/001-ingredient-taxonomy-contract.md) | Ingredient taxonomy contract |
| [adr/002-canonical-taxonomy-before-backup.md](adr/002-canonical-taxonomy-before-backup.md) | Taxonomy hardening before backup contract |
| [adr/003-household-tenancy-and-authorization.md](adr/003-household-tenancy-and-authorization.md) | Household tenancy and authorization |
| [adr/004-draft-first-recipe-authoring-and-external-identifiers.md](adr/004-draft-first-recipe-authoring-and-external-identifiers.md) | Draft-first authoring, proposal workflow, localization identity, serving scaling, external IDs |

## Operations (runbooks)

| Document | Topic |
| --- | --- |
| [operations/restore.md](operations/restore.md) | Restore from JSON export or pg_dump |
| [operations/releases.md](operations/releases.md) | Version tags and release workflow |
| [operations/coderabbit.md](operations/coderabbit.md) | PR review with CodeRabbit |

## Historical / frozen

| Location | Role |
| --- | --- |
| [releases/](releases/) | Per-version release notes — **do not edit** after ship |
| [archive/](archive/) | Phase handoffs and other transient docs kept for context |

## Agent workflow

[AGENTS.md](../AGENTS.md) — tool responsibilities and work modes for AI-assisted development.

## Entry point

[README.md](../README.md) — how to run and test the app; links here for documentation.

# ADR 004 — Draft-First Recipe Authoring And External Identifiers

## Document metadata

- **Purpose:** Durable decisions for AI-assisted recipe authoring, ingredient proposals, recipe drafts, localization identity, serving scaling, and opaque external identifiers.
- **Authority:** Canonical ADR for Phase 16C+ authoring architecture; feature detail in [features/ingredient-proposals.md](../features/ingredient-proposals.md), [features/recipe-import-drafts.md](../features/recipe-import-drafts.md), and [features/localization.md](../features/localization.md).
- **Status:** Accepted — architecture for upcoming Phase 16 slices.
- **Update when:** A later ADR supersedes recipe authoring trust boundaries, translation identity, scaling semantics, or external identifier policy.

**Status:** Accepted (July 2026)  
**Context:** Phase 16 moves MealRoulette from manual recipe CRUD toward controlled recipe ingestion: users describe or paste recipes, the application structures them, resolves ingredients against the canonical catalog, proposes missing ingredients when needed, and later supports reviewed localization and LLM-assisted authoring.

## Decision

MealRoulette will use a draft-first, deterministic authoring workflow.

```text
User input
  -> LLM or manual extraction into a draft
  -> deterministic ingredient resolution
  -> user review
  -> deterministic validation
  -> explicit commit into trusted recipe tables
```

The core rule:

```text
LLM decides what to suggest.
Application services decide what is valid.
User decides what to accept.
Platform admin decides what enters global taxonomy.
```

## Ingredient Proposals

Ingredient proposals are a governed unresolved-catalog workflow, not an isolated admin form.

They are reusable infrastructure for:

- manual recipe editing;
- recipe import drafts;
- LLM-assisted recipe authoring;
- fixture/import workflows;
- future public recipe adoption.

Household users may propose missing ingredients. Only `platform_admin` may approve catalog mutation. A proposal may resolve as a new canonical ingredient, mapping to an existing ingredient, adding an alias, rejection, withdrawal, or a request for more information.

Active recipes used by planning and shopping must never reference unresolved proposal text.

## Recipe Drafts

Recipe import and authoring flows must persist drafts before they create trusted dishes or recipes.

Only an explicit commit command may create or update:

- `dishes`;
- `recipes`;
- `recipe_ingredients`;
- `recipe_steps`.

Activation invariant: a committed active recipe must have approved canonical ingredients, known units, valid quantities, ordered steps, valid timers/temperatures, household ownership, no unresolved required proposal, and explicit user confirmation.

## LLM Tooling

LLM integration must use narrow application tools and structured outputs. It must not receive generic SQL access or unrestricted trusted-data CRUD.

Allowed tool categories:

- search global ingredients and aliases;
- inspect taxonomy/unit options;
- mutate only the current draft;
- create an ingredient proposal;
- run deterministic validation.

Disallowed model tools:

- create or approve canonical ingredients;
- publish or commit recipes;
- delete trusted recipes;
- restore/import backups;
- bypass household authorization.

Start with one recipe-authoring orchestrator and deterministic services. Do not introduce multi-agent swarms until there is evidence that a pipeline cannot solve the problem.

## Localization Identity

Recipe, dish, and ingredient identities are language-independent.

Do not make core `recipes` rows keyed by `(recipe_id, language_id)`. Use translation tables keyed by `(entity_id, locale)` for localized representations.

Examples:

- `recipes.id` identifies the recipe structure.
- `recipe_translations(recipe_id, locale)` stores localized variant name, description, and notes.
- `recipe_step_translations(recipe_step_id, locale)` stores localized instructions.
- `dish_translations(dish_id, locale)` stores localized dish names and descriptions.

Structured data remains shared across locales: ingredients, quantities, units, timers, temperatures, servings, recipe type, difficulty, and source URL.

## Serving Scaling

Recipes store reference yield/servings and original quantities. Meal planning or cooking may request a target serving count, producing a scaling factor.

Do not rewrite stored recipe quantities for each serving count.

Initial model:

- `recipes.reference_servings`;
- `meal_plan_items.servings_planned` when a planned meal differs from reference;
- recipe ingredient scaling rules such as `linear`, `rounded_count`, `to_taste`, and `fixed`.

Ingredient quantities may scale. Cooking times do not automatically scale.

Shopping uses scaled exact quantities as input, then applies the existing aggregation, conversion, and display-rounding rules.

## External Identifiers

Sequential database IDs may remain internal implementation identifiers.

New user-facing, cross-household, shareable, or public-catalog identifiers must be opaque and stable. Do not derive public identifiers by hashing sequential IDs or predictable strings such as `recipe1`.

Use UUID/ULID-style public identifiers or existing stable public keys where they already fit the product semantics.

Internal joins may continue using current primary keys unless a migration has a concrete product need.

## Consequences

- Phase 16C remains ingredient proposals, but its design must support future recipe drafts and LLM imports.
- Recipe draft/import infrastructure must precede real LLM authoring.
- Localization foundation must separate source entities from translated representations.
- Public identifiers should be added gradually at external API/public-catalog boundaries, not by rewriting the whole schema.

## Rejected Alternatives

- **Autonomous agent edits trusted data directly:** rejected because it bypasses validation, authorization, and audit boundaries.
- **Ingredient proposals as platform-only admin CRUD:** rejected because recipe authoring needs a governed unresolved-catalog workflow.
- **Localized recipes as core recipe rows:** rejected because it duplicates language-independent structure and invites cross-language semantic drift.
- **Hash sequential IDs for public identifiers:** rejected because it is predictable in shape, brittle, and unnecessary when UUID/ULID identifiers are available.

## References

- [ADR 001 — Ingredient taxonomy contract](001-ingredient-taxonomy-contract.md)
- [ADR 002 — Canonical taxonomy and computed scheduler targets before backup contract](002-canonical-taxonomy-before-backup.md)
- [ADR 003 — Household tenancy and authorization](003-household-tenancy-and-authorization.md)
- [Ingredient Proposals](../features/ingredient-proposals.md)
- [Recipe Import Drafts](../features/recipe-import-drafts.md)
- [Localization and Translation](../features/localization.md)

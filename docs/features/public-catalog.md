# Public Catalog

## Document metadata

- **Purpose:** Authenticated MealRoulette public recipe catalog — publication, moderation, immutable snapshots, and household adoption.
- **Authority:** Feature specification for Phase 16D; strategy context in [public-catalog-contribution-and-rewards.md](../strategy/public-catalog-contribution-and-rewards.md); tenancy in [ADR 003](../adr/003-household-tenancy-and-authorization.md); identifiers in [ADR 004](../adr/004-draft-first-recipe-authoring-and-external-identifiers.md).
- **Status:** Implemented — Phase 16D foundation.
- **Update when:** Publication states, snapshot shape, adoption semantics, or catalog visibility rules change.

---

## Audience

The **MealRoulette public catalog** is **authenticated-public**: any signed-in household member may browse approved public recipes and adopt them.

It is **not** anonymous web-public. Open web discovery is a later phase.

## Product model

```text
household recipe
  -> publish/submit (household admin)
  -> public_recipes (lineage) + public_recipe_versions (immutable snapshot)
  -> platform approve
  -> discoverable in catalog
  -> adopt
  -> new household Dish + Recipe (copy) with provenance
```

Household edits after publication do **not** mutate published snapshots.

## Statuses

`public_recipes.status`:

| Status | Meaning |
| --- | --- |
| `submitted` | Awaiting platform review; not discoverable |
| `public` | Approved and discoverable (`current_version_id` set) |
| `rejected` | Rejected; may be resubmitted |
| `withdrawn` | Withdrawn by household while submitted; may be resubmitted |
| `delisted` | Removed from discovery; existing adopters keep copies |

## Resubmission

Unique lineage per `originating_recipe_id`:

- `submitted` or `public` → new submit returns **409**
- `rejected` or `withdrawn` → resubmit creates a **new immutable version number** under the same `public_recipes` row; status returns to `submitted`; `current_version_id` stays null until approval
- `delisted` → new submit returns **409** in Phase 16D (republish UX later)

Phase 16D supports **one live approved version** at a time.

## Versions and timestamps

- Snapshot is created at **submit** time (`created_at`).
- `published_at` is **nullable** and set only when platform **approves**.
- `current_version_id` is **null** until approval.
- Public list/detail require `status=public` and non-null `current_version_id`.

## Snapshot contents

Must be sufficient to recreate household dish/recipe/ingredients/steps (see implementation). Denormalized ingredient/unit display fields are included for stable public read.

Submit requires a **complete** source recipe: at least one ingredient and at least one step (422 otherwise).

## Adoption

Creates a **new Dish + Recipe** in the adopting household, **preserving** source dish/recipe semantics (`meal_composition`, `simple_dish_part`, `course`, `recipe_type`, `is_main`, etc.). Does not force “main recipe” semantics.

Adoption is a **single transaction**: dish, recipe, ingredients, steps, and provenance commit together; a mid-copy failure leaves no partial dish/recipe.

Provenance on the adopted recipe:

- `derived_from_public_recipe_id`
- `derived_from_public_version_id`

Delisting hides discovery but does not delete adopted copies.

## Source deletion

While a lineage is `submitted` or `public`, deleting the originating dish or recipe returns **409**. Withdraw (household) or delist (platform) first. Origin FKs remain `ON DELETE CASCADE` for withdrawn/rejected/delisted cleanup; nullable origin FKs with `SET NULL` are a later model option.

## Attribution

Public member DTOs expose snapshot title/description and version metadata only. Originating household/user identifiers are not shown to members.

## Authorization

- Household admin: submit, list own publication requests, withdraw while `submitted`
- Household member: browse public catalog, adopt
- Platform admin: list all, approve (optional note), reject/delist (required note)

## Non-goals (Phase 16D)

- Contribution rewards / credits / rankings / badges
- Anonymous web catalog
- LLM moderation
- Recipe drafts / localization
- Attach adopt to an existing dish
- Multi-live-version republish UX
- Public comments/reviews

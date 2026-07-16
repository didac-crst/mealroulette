# ADR 003 — Household tenancy and authorization

## Document metadata

- **Purpose:** Durable decisions for users, households, authorization boundaries, ratings, Telegram linking, and backup scope.
- **Authority:** Canonical ADR for Phase 15 tenancy and authorization; feature delivery status in [BACKLOG.md](../BACKLOG.md).
- **Status:** Implemented — Phase 15A–E on `main` (PRs #17–#21); closeout in 15F.
- **Update when:** A later ADR supersedes identity, tenancy, role, rating, Telegram, or backup ownership decisions.

**Status:** Implemented (July 2026) via Phase 15A–E  
**Context:** MealRoulette previously had global `admin` / `user` roles, global dishes/recipes/plans/settings, singleton scheduler/Telegram/backup settings, and user-linked cooking timer alerts. Phase 15 introduced household collaboration without corrupting global ingredient taxonomy or leaking data across households.

## Decision

MealRoulette will use a household tenancy model with separate platform and household authorization domains.

1. **Users are global identities.**
2. **Households are tenant boundaries.**
3. **Memberships connect users to households and carry household roles.**
4. **Platform roles are separate from household roles.**
5. **Ingredients, units, food groups, ingredient families, aliases, and conversions are global platform-governed reference data.**
6. **Dishes, recipes, meal plans, planning rules, shopping lists, ratings, reviews, household notification defaults, and household integrations are household-owned.**

The word `admin` must not be used alone in new authorization APIs or domain models.

## Roles

Initial platform role:

- `platform_admin`: may manage global catalogue/taxonomy data, platform operations, and whole-database backup/restore.

Initial household roles:

- `household_admin`: may manage household members, invitations, household settings, and household-owned meal-planning content.
- `household_member`: may use household planning, shopping, cooking, review, reroll, and collaborative recipe workflows.

Platform administration does not imply invisible household membership or unrestricted private household access. Any future support/impersonation flow must be explicitly designed and audited.

## Identity Keys

Use UUID primary keys for new identity, tenancy, and security-sensitive tables:

- `users`
- `households`
- `household_memberships`
- `household_invitations`
- `user_platform_roles`
- Telegram link/account/subscription tables
- audit events

This is acceptable because current installations are small and user data is still early. UUIDs reduce user enumeration risk and are a better fit for invitation links, public-safe references, and future multi-household use.

Do **not** migrate existing content tables to UUIDs as part of Phase 15:

- dishes
- recipes
- meal plans and meal-plan items
- shopping lists
- ingredients, units, taxonomy tables
- scheduler/planning content

Keep their integer primary keys unless a later external/public API needs opaque stable identifiers. Existing public keys on dishes/recipes remain separate from database primary keys.

## Household Ownership

Add `household_id` to root household aggregates first:

- `dishes`
- `meal_plans`
- `planning_rules`
- `shopping_lists`
- household scheduler settings or equivalent household scheduling configuration
- household Telegram/notification defaults

Recipes inherit ownership through `dishes`. Recipe steps and ingredients inherit through `recipes`. Meal-plan items and lines inherit through `meal_plans`.

Service methods must accept an actor/context and enforce household ownership. Route-level dependencies are necessary but not sufficient.

## Signup And Invitations

Initial supported flows:

1. Atomic signup creates:
   - user;
   - household;
   - active `household_admin` membership.
2. Household admin creates a single-use, time-limited invitation.
3. Invitation acceptance creates an active `household_member` membership.
4. Promotion to `household_admin` happens after joining.

Households must always retain at least one active household admin. Demoting, removing, or leaving as the last admin must fail.

Do not add public household discovery. Joining an existing household requires a deliberate invitation.

## Ratings And Reviews

MealRoulette needs two related but distinct feedback concepts.

### Recipe Preference

A user-level recipe or dish preference answers:

> Do I generally like this dish or recipe?

Recommended shape:

```text
recipe_ratings
- id UUID or integer PK
- household_id
- user_id
- dish_id
- recipe_id NULL
- rating
- comment NULL
- created_at
- updated_at
- UNIQUE (household_id, user_id, recipe_id)
```

When rating a dish without a specific recipe, use a separate dish-rating row or a nullable recipe strategy with a constraint that prevents ambiguous duplicates.

### Meal-Slot Review

A meal-slot review answers:

> Was this meal right in this context: this package or main course, on this weekday, date, month, and lunch/dinner slot?

Keep this connected to `meal_plan_items` and the actual meal package shown/eaten. It should preserve historical context and should not be collapsed into a single dish-level rating.

Recommended shape:

```text
meal_reviews
- id UUID or integer PK
- household_id
- meal_plan_item_id
- user_id
- rating NULL
- outcome/status context
- comment NULL
- created_at
- updated_at
- UNIQUE (meal_plan_item_id, user_id)
```

Current `meal_ratings` should evolve toward this model rather than being replaced by dish-only unique ratings.

## Global Catalogue Governance

All active household users may read global reference data.

Only `platform_admin` may mutate:

- ingredients;
- ingredient aliases;
- food groups;
- ingredient families;
- units;
- ingredient-specific conversions;
- taxonomy imports or repair actions.

Household users who need missing ingredients should use an ingredient proposal workflow. Recipe drafts may hold unresolved ingredient text, but active recipes used for planning/shopping must reference approved global ingredients.

## Telegram And Notifications

Telegram links to a specific MealRoulette user, not directly to a household.

Initial model:

- user-level Telegram account/link established through a single-use bot deep-link token;
- household notification defaults define what the household normally sends;
- per-user subscriptions define whether a user receives a given household event through Telegram.

Cooking timers are owned by the user who starts them and should notify that user by default. Household-wide timer broadcasts are out of scope.

## Backup Scope

Whole-database backup/restore is a platform operation, controlled by `platform_admin`.

For self-hosted MealRoulette, database-level backup is the preferred recovery mechanism for now. Household-level portable export/import is deferred because it requires a separate public contract for household-owned data, global catalogue references, publication state, and cross-household provenance.

Existing JSON backup/export may remain as an operational tool, but multi-household semantics should not treat it as a household-admin data portability feature until explicitly redesigned.

## Deferred Scope

The following are intentionally out of scope for Phase 15 (remain future work):

- public recipe publication and moderation;
- localization tables for dishes, recipes, and steps;
- cross-household recipe copy/adopt workflows;
- granular custom permissions beyond the three initial roles;
- platform support impersonation;
- Telegram group-chat support;
- Telegram OTP / passwordless bot login;
- password / account settings UI;
- ingredient proposal workflow;
- user-level recipe preference API/UI (`recipe_ratings`);
- multi-household membership;
- passkeys;
- PostgreSQL row-level security;
- household-level portable export/import.

## Migration Strategy

Implemented as stacked PRs (not the umbrella branch):

| ADR slice | Shipped as | PR |
| --- | --- | --- |
| Slice 1 — Identity And Tenancy | Phase 15A | [#17](https://github.com/didac-crst/mealroulette/pull/17) |
| Slice 2 — Household Ownership | Phase 15B | [#18](https://github.com/didac-crst/mealroulette/pull/18) |
| Slice 3 — Authorization Split | Phase 15B–D (platform vs household dependencies + UI gates) | [#18](https://github.com/didac-crst/mealroulette/pull/18)–[#20](https://github.com/didac-crst/mealroulette/pull/20) |
| Slice 4 — Invitations | Phase 15C–D | [#19](https://github.com/didac-crst/mealroulette/pull/19)–[#20](https://github.com/didac-crst/mealroulette/pull/20) |
| Slice 5 — Ratings, Telegram, And Notifications | Phase 15B meal reviews + Phase 15E Telegram | [#18](https://github.com/didac-crst/mealroulette/pull/18), [#21](https://github.com/didac-crst/mealroulette/pull/21) |

### Implementation notes vs original draft

- Greenfield installs create households via signup; a migration default household remains only for upgrading legacy single-tenant data.
- Users may hold **at most one active household membership** in the initial product.
- Meal-slot reviews shipped by evolving `meal_ratings` → `meal_reviews` (user + household scoped). Separate user-level `recipe_ratings` preference remains deferred.
- Ingredient proposal architecture remains deferred; household users still cannot create missing global ingredients.
- Telegram OTP / passwordless bot login and password settings UI remain deferred.

### Original staged outline (historical)

#### Slice 1 — Identity And Tenancy

1. Add UUID-backed `households` and `household_memberships`.
2. Migrate or recreate `users` as UUID-backed identities while preserving the existing single test/admin user.
3. Create one default household.
4. Convert current users into members of that household.
5. Map trusted current admin/operator to `platform_admin` and `household_admin`.

#### Slice 2 — Household Ownership

1. Add `household_id` to household root aggregates.
2. Backfill existing rows to the default household.
3. Add non-null and foreign-key constraints after validation.
4. Scope read/write services by active household.
5. Add two-household tenant isolation tests.

#### Slice 3 — Authorization Split

1. Replace `get_current_admin` usage with explicit platform/household policy dependencies.
2. Move global catalogue mutation behind platform-admin authorization.
3. Keep global catalogue reads available to household members.
4. Add ingredient proposal architecture before allowing household users to request missing catalogue entries.

#### Slice 4 — Invitations

1. Add invitation tokens stored only as hashes.
2. Support single-use invitation acceptance.
3. Add household membership management UI.
4. Enforce last-admin protection.

#### Slice 5 — Ratings, Telegram, And Notifications

1. Split recipe preference from meal-slot review.
2. Link Telegram accounts to users through one-time bot deep links.
3. Add household notification defaults plus user subscriptions.
4. Deliver scheduled notifications by resolving current active memberships/subscriptions at send time.

## Consequences

- The current `users.role` model is deprecated.
- Existing route dependencies and service methods need systematic authorization refactoring.
- Many tests must gain at least two-household coverage to prove tenant isolation.
- Integer content IDs remain acceptable internally because all household-owned access is scoped by household context.
- UUID user and household IDs make invitation, membership, and future multi-household flows safer and cleaner.

## References

- [BACKLOG.md](../BACKLOG.md)
- [CURSOR_ROADMAP.md](../CURSOR_ROADMAP.md)
- [SPECS.md](../../SPECS.md)
- [Backup Export and Import](../features/backup-export-import.md)
- [Telegram and cooking-mode notes](../features/cooking-mode.md)

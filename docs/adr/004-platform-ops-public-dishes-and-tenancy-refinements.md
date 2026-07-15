# ADR 004 — Platform ops, public dishes, and tenancy refinements

## Document metadata

- **Purpose:** Capture accepted refinements to Phase 15 tenancy and future public-dish publication architecture.
- **Authority:** Canonical ADR for platform/household separation refinements and future public-dish publication model.
- **Status:** Accepted — Phase A applies to Phase 15; Phases B-D are future implementation phases.
- **Supersedes / amends:** Amends and extends [ADR 003 — Household tenancy and authorization](003-household-tenancy-and-authorization.md). Does not replace it.
- **Update when:** Accepted, rejected, or split into multiple ADRs.

**Context:** Phase 15 implementation work surfaced two refinements to ADR 003. First, platform operators and household users need cleaner separation than a bootstrap user that automatically wears both hats. Second, public dish sharing is desirable, but it must not distract from finishing Phase 15 user, household, membership, and authorization implementation. This ADR accepts the tenancy refinements for Phase 15 and records public-dish/publication rules for future phases.

---

## Summary of decisions (confirmed)

The following reflect owner-approved direction from design discussion (July 2026):

1. **Platform admin and household membership are orthogonal.** Platform operators are not implicitly members of a household.
2. **No default household on greenfield installs.** All households are created deliberately (signup or operational import). A migration default household remains acceptable only for upgrading existing single-tenant data.
3. **One active household per user (initial product constraint).** A user may hold at most one active `household_membership`. Multi-household membership is deferred.
4. **Platform admins are created only via operator tooling** (interactive shell script), not public web signup.
5. **Household creation is a public web flow** on the login site: user + household name + credentials in one atomic step.
6. **Dishes are private by default;** future phases may let owners publish them to a shared catalog after checks pass.
7. **Dish identity is stable** when toggling private ↔ public (same primary key and `public_key`; visibility is a property, not a new entity).
8. **Public catalog is browsable** by all authenticated household users; **using** a foreign dish in planning requires **subscription** (see below).
9. **Consumers of public dishes are read-only** on canonical content (no edit of owner rows).
10. **Translations** use a locale overlay on canonical entities (same `recipe_id` / `recipe_step_id`), not duplicate recipe rows per language.
11. **Dish translation in locale L is required** before any recipe translation in the same locale L may be approved.
12. **Translation requests** may be opened by the **owner** or a **subscribing consumer**; approval remains with the owner (or platform admin for system-owned dishes).
13. **Publication revalidation** after edits uses a tiered model (see below), not blind auto-demote on every change.
14. **Initial publication and revalidation checks** are enforced by an automated script. If checks pass, the owner may publish; platform admins handle failed checks, edge cases, moderation, and `pending_revalidation` review.

---

## Relationship to ADR 003

| ADR 003 | This ADR |
| --- | --- |
| Separate platform vs household roles | **Confirm** — tighten implementation so platform admin has no default household |
| Default household for migration | **Amend** — greenfield installs must not rely on a product “default household” |
| Defer public publication | **Confirm for Phase 15** — publication design is specified here but implemented in a future phase |
| Defer localization tables | **Partially revise** — translation *rules* for public dishes are specified; full Phase 17 job pipeline still deferred |
| Integer PKs for dishes/recipes | **Confirm** — keep integer PKs; `public_key` remains stable external identifier |

---

## Platform administration

### Creation

Platform admins are created through an operator-facing command (evolution of `bootstrap_admin`):

- Prompt for username, password, password confirmation.
- Create user with `user_platform_roles.platform_admin` only.
- **Do not** create or attach a `household_membership`.

Public endpoints must not create platform admins.

### UI and API surface

Platform admins **without** a household membership must not use household workflows:

- **Excluded:** Today, Plan, Review, Shopping (require `HouseholdScope`).
- **Included:** global ingredients/taxonomy, backups, user/platform ops, **cross-household dish registry** (administrative list, not the household gallery).

If the same person also wants meal planning, they must **explicitly** create or join a household through the normal signup or invite flows (wearing two hats).

### Cross-household dish registry

In a future platform-ops/public-catalog phase, platform admins need a read-oriented **registry** of all dishes showing at minimum:

- dish identity (`id`, `public_key`);
- dish name (source locale);
- owner household (id + display name);
- visibility / publication status;
- recipe count, updated timestamp.

This is moderation/ops UI (table/filters), not the household dish gallery. It does not grant edit access to private household content.

---

## Household tenancy refinements

### Greenfield vs migration

| Install type | Household bootstrap |
| --- | --- |
| **New (greenfield)** | No pre-created household. First household appears via signup or operator import targeting an explicit `household_id`. |
| **Upgrade (existing data)** | One migration household may backfill legacy rows. It should be renameable to a real household name; it is not a special product tenant. |

Household display names are **not** globally unique. Household **UUID** is the identity. Username remains globally unique.

### Signup and invitations (unchanged semantics, clarified UI)

| Flow | Entry | Result |
| --- | --- | --- |
| **Create household** | Login site — “Sign up” | New user + new household UUID + `household_admin` |
| **Join household** | `/join?token=…` | New or existing user + `household_member` (or reactivation) |
| **Invite** | Household admin | Single-use hashed token, time-limited |

Enforce **at most one active membership** per user:

- Signup fails if user already has an active membership.
- Invite acceptance fails if user already belongs to another household (until leave flow exists).

### Platform admin vs household admin (recap)

| Capability | `platform_admin` | `household_admin` |
| --- | --- | --- |
| Global ingredients/taxonomy | yes | read only |
| Backups (whole DB) | yes | no |
| Household members/invites | no | yes |
| Own household dishes/plans | only if also a member | yes |
| Public catalog browse | yes (when also a member) | yes |
| Dish registry (all households) | yes | no |

---

## Public dishes and catalog

Public dish publication is **not** part of Phase 15 completion. Phase 15 must finish users, households, memberships, route/service authorization, household scoping, and platform-vs-household navigation. The following model is accepted for later implementation.

### Ownership and visibility

Every dish row has:

- `household_id` — owning household (always set).
- `visibility` — `private` (default) | `public`.
- `publication_status` — `not_published` | `published` | `pending_revalidation` | `rejected`.
- `published_at`, `published_by_user_id` — nullable audit fields.

**System / seed dishes** are public dishes owned by a designated platform/system household UUID, not a separate table. This system household is not a normal household: it has no memberships, is excluded from household switchers and household signup/invite flows, and is managed by platform tooling.

Toggling `private` → `public` or the reverse **must not** change `dishes.id` or `dishes.public_key`.

### Catalog vs subscription

| Action | Requirement |
| --- | --- |
| Browse/search **public** dishes | Any authenticated household member |
| View public recipe (read-only) | Any authenticated household member |
| Add foreign dish to meal plan / roulette | Active **subscription** for `(consumer_household_id, source_dish_id)` |
| Edit dish/recipe | Owner household only |

Recommended shape:

```text
household_dish_subscriptions
  id                UUID PK
  household_id      UUID FK households  -- consumer
  source_dish_id    INT FK dishes       -- canonical owner row
  subscribed_at     timestamptz
  UNIQUE (household_id, source_dish_id)
```

**Unresolved (product):** explicit “Add to my library” vs automatic subscription on first plan use. Both satisfy “catalog available”; pick one in implementation.

If the owner **unpublishes** a dish:

- historical meal-plan references remain readable;
- new planning, roulette, and shopping generation must not newly select the unpublished foreign dish;
- existing subscriptions become inactive or archived, not hard-deleted;
- future fork/copy behaviour remains deferred.

### Forking (deferred)

Copying a public dish into an editable household-owned fork is **out of scope** for the first publication slice. Consumption is reference + read-only unless/until a fork ADR is added.

---

## Publication checks

### Who runs checks

1. **Automated script** (deterministic, idempotent) — required on initial publish and on revalidation.
2. **Owner publish on pass** — when checks pass, an owner household admin may publish or clear revalidation.
3. **`platform_admin`** — handles failed checks, moderation, edge cases, and forced unpublish.

Owners initiate “Make public” or “Request revalidation”; they do not self-approve script failures.

### Minimum rules (initial set — extensible)

Script should verify at least:

- dish has at least one recipe marked main (or agreed main-recipe rule);
- main recipe has non-empty steps;
- recipe ingredients resolve to approved global ingredients (no unresolved draft lines for public use);
- locale invariants (see Translations) if translations are present.

Exact rule set may grow; failures return structured reasons to the owner.

### Revalidation after edit (recommended policy)

Avoid demoting to `private` on every edit.

| Edit class | Public listing | Translations | `publication_status` |
| --- | --- | --- | --- |
| **Cosmetic** (wording in source locale, notes) | stays public | mark affected locales `stale` | unchanged |
| **Structural** (ingredients, steps, times, servings, recipe set) | stays public | mark all locales `stale` | → `pending_revalidation` |
| **Fails minimum viability** | cannot remain public for new use | — | block save or set `visibility=private`, `publication_status=rejected` |

After `pending_revalidation`, dish remains in catalog with a visible “updated — review pending” state until script checks pass and owner/platform action clears it.

**Rejected alternative:** auto-demote to `private` on any structural edit (harms subscribers and catalog stability).

---

## Translations and public dishes

Implementation should align with [features/localization.md](../features/localization.md) (`translations` table, `default_locale`, draft/approved/stale lifecycle).

### Translatable fields (publication slice)

| Entity | Fields |
| --- | --- |
| Dish | `name`, `description` (and `notes` if retained) |
| Recipe | `variant_name`, `description`, `notes` |
| Recipe step | `instruction` |
| Recipe ingredient line | `notes` (optional) |

Dish structural fields (bools, enums, tags, traits JSON) are not translated.

### Locale coverage rule (confirmed)

For each dish and locale `L`:

1. An **approved dish translation** for locale `L` must exist before any **approved recipe translation** for the same `(dish, L)` may exist.
2. Partial recipe coverage is allowed (e.g. dish in FR + one of two recipes in FR).
3. Recipe translation in locale `L` without dish translation in `L` is **invalid** — reject at approval time.

Example (valid):

- Dish EN + recipes A,B in EN.
- Dish FR + recipe A in FR only.

Example (invalid):

- Dish EN only; recipe A ES translation — reject.

### Translation requests

```text
translation_requests
  id                      UUID PK
  requester_user_id       UUID FK users
  requester_household_id  UUID FK households
  entity_type               dish | recipe | recipe_step | recipe_ingredient
  entity_id                 integer
  target_locale             BCP-47 base locale
  status                    pending | approved | rejected | completed
  created_at
  resolved_at               nullable
  resulting_translation_id  nullable FK translations
```

- **Owner** may request translations for their public (or private) content.
- **Subscribing consumer** may request translations for public dishes they do not own.
- **Owner** (or platform admin for system household dishes) approves requests and resulting draft translations.

Consumers never write approved translations directly on canonical owner rows.

---

## Stable identifiers

| Entity | Internal PK | Stable external id |
| --- | --- | --- |
| User | UUID | UUID |
| Household | UUID | UUID |
| Dish | integer | `public_key` (existing; immutable on rename) |
| Recipe | integer | `public_key` (existing) |

Adding a separate `dishes.uuid` column is **optional**; not required if `public_key` remains the cross-system identifier. If added later, it must be assigned at creation and never rotated on visibility changes.

**Confirmed:** private and public are the **same row**; visibility is not a copy.

---

## Implementation phases (recommended)

### Phase A — Finish Phase 15 tenancy/users

1. `bootstrap_platform_admin` — no household membership.
2. Login **Sign up** page (`POST /api/auth/register`).
3. Enforce single active membership in signup/invite services.
4. Nav/route gating: platform-only vs household-required.
5. Greenfield migration path without default household insert (new revision); document upgrade path for existing DBs.

This is the scope required to finish Phase 15. Publication, subscriptions, and translations must not block Phase 15 completion.

### Phase B — Platform registry

1. Platform-scoped dish list API + admin UI.
2. No publication yet — visibility column may default to `private`.

### Phase C — Publication foundation

1. `visibility`, `publication_status`, audit columns on dishes.
2. Publication/revalidation checks + platform moderation workflow.
3. Public catalog API (read).
4. `household_dish_subscriptions` + planning integration for foreign dishes.

### Phase D — Translations for public dishes

1. `translations` + `default_locale` foundation (per localization.md).
2. Locale coverage enforcement.
3. `translation_requests` workflow.

---

## Unresolved decisions (require human confirmation before implementation)

1. **Subscription UX:** explicit library add vs auto-subscribe on first plan use.
2. **System household UUID:** fixed constant vs migration-created singleton.
3. **`dish.notes`:** keep as translatable field or deprecate for metadata-only dish row.
4. **Multi-household users:** deferred; schema may allow later but product enforces one active membership now.

---

## Consequences

- ADR 003 migration slice “create default household” becomes **upgrade-only**; product docs must not describe a permanent default tenant.
- Bootstrap and test fixtures need splitting: platform admin fixtures vs household signup fixtures.
- Catalog service gains two modes: household-scoped (own + subscribed) and platform-scoped (registry).
- Localization implementation must enforce dish-before-recipe locale rules for public content.
- Phase 15 remains focused on users, households, memberships, tenancy, and authorization.
- Public recipe publication and public catalog subscriptions move from deferred to **planned future work** under this ADR’s phases C-D.

---

## References

- [ADR 003 — Household tenancy and authorization](003-household-tenancy-and-authorization.md)
- [features/localization.md](../features/localization.md)
- [features/computed-traits.md](../features/computed-traits.md) — `public_key` semantics
- [BACKLOG.md](../BACKLOG.md)
- [SPECS.md](../../SPECS.md)

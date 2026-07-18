# Ingredient Proposals

## Document metadata

- **Purpose:** Governed missing-ingredient proposal workflow for household users, recipe drafts, imports, and platform catalog review.
- **Authority:** Feature specification for Phase 16C; architecture in [ADR 004](../adr/004-draft-first-recipe-authoring-and-external-identifiers.md).
- **Status:** Implemented — Phase 16C foundation.
- **Update when:** Proposal states, review outcomes, authorization, or integration with recipe drafts changes.

---

Ingredient proposals are the controlled way to evolve the global ingredient catalog when recipe entry encounters something unresolved.

They are not trusted ingredients. They are requests that a platform admin may resolve.

## Goals

- Let household users submit missing or ambiguous ingredient requests without mutating the global catalog.
- Give platform admins a review queue with enough culinary and locale context to decide correctly.
- Support future recipe drafts and LLM-assisted recipe authoring by linking unresolved draft ingredients to proposals.
- Preserve the taxonomy contract from [ADR 001](../adr/001-ingredient-taxonomy-contract.md).

## Non-goals

- No automatic approval.
- No LLM provider integration in Phase 16C.
- No public catalog workflow.
- No recipe draft extraction in Phase 16C, beyond optional source-link fields.
- No direct household-user mutation of ingredients, aliases, families, food groups, units, or conversions.

## Proposal Sources

`source_type` values:

- `manual`
- `recipe_editor`
- `recipe_import`
- `llm_recipe_import`
- `bulk_import`
- `platform_admin`

`source_reference_type` and `source_reference_id` may link a proposal to a draft ingredient, recipe draft, import session, or future import job. These fields are optional until those systems exist.

## Data Model

```text
ingredient_proposals
- id UUID
- proposed_name
- normalized_name
- source_locale
- description NULL
- culinary_context NULL
- suggested_food_group_id NULL
- suggested_family_id NULL
- suggested_storage_class NULL
- suggested_product_form NULL
- suggested_preservation NULL
- resolution_status
    pending
    needs_information
    duplicate
    approved
    rejected
    withdrawn
- resolution_type NULL
    created_canonical
    mapped_existing
    added_alias
    rejected
- resolved_ingredient_id NULL
- proposed_by_user_id
- household_id NULL
- source_type
- source_reference_type NULL
- source_reference_id NULL
- model_provider NULL
- model_name NULL
- model_confidence NULL
- model_reasoning_summary NULL
- reviewed_by_user_id NULL
- reviewed_at NULL
- review_note NULL
- created_at
- updated_at
```

`household_id` is retained for provenance and user visibility. It does not make the proposed ingredient household-owned.

## State Transitions

```text
pending
  -> needs_information
  -> duplicate
  -> approved
  -> rejected
  -> withdrawn

needs_information
  -> pending
  -> rejected
  -> withdrawn
```

Terminal states:

- `duplicate`
- `approved`
- `rejected`
- `withdrawn`

## Resolution Outcomes

`mapped_existing`:

- The proposal was already represented by an existing canonical ingredient.
- Set `resolved_ingredient_id`.

`added_alias`:

- The proposal should become an alias of an existing canonical ingredient.
- Set `resolved_ingredient_id`.
- Create the alias through the normal platform-admin alias workflow.

`created_canonical`:

- The proposal satisfies the taxonomy granularity contract and becomes a new canonical ingredient.
- Set `resolved_ingredient_id` to the created ingredient.

`rejected`:

- The proposal is not appropriate for the catalog.
- Preserve `review_note`.

## Authorization

Household members:

- create proposals for their active household;
- list their own proposals;
- withdraw their pending proposals.

Household admins:

- same as members;
- may see household proposals if product UI needs it later.

Platform admins:

- list all proposals;
- review and resolve proposals;
- create canonical ingredients, aliases, or mappings as explicit review actions.

Primary UI surfaces:

- `/ingredients` — single **Ingredient proposals** entry for household users; **Proposal review** for platform admins;
- `/ingredients/proposals` — Propose / My proposals tabs;
- `/ingredients/proposal-review` — platform review queue.

Canonical names are internal snake_case slugs (e.g. `torch_ginger_flower`). Members submit free-text proposed names.
Rejected proposals are immutable history and do **not** reserve or ban a name; only an existing `ingredients.canonical_name` blocks approve-new.

Review actions that mutate the catalog (`add-alias`, `approve-new`) apply the catalog write and the proposal review fields in a **single database transaction**. Catalog helpers flush without committing when called from proposal review so a failed review update cannot leave an orphan alias or ingredient.

Platform admin access to proposals does not imply unrestricted access to private household recipe drafts. Proposal fields must contain enough review context without exposing full private recipe content unless a future audited support flow is designed.

## Deduplication

On create:

- normalize `proposed_name`;
- search pending proposals with matching normalized name and source locale;
- search existing ingredients and aliases;
- return possible matches to the user where practical.

Do not silently merge proposals across households. If an existing pending proposal is similar, link or display it for platform review, but preserve the new submitter's provenance.

## API Sketch

```text
POST /api/ingredient-proposals
GET  /api/ingredient-proposals/mine
POST /api/ingredient-proposals/{proposal_id}/withdraw

GET  /api/platform/ingredient-proposals
GET  /api/platform/ingredient-proposals/{proposal_id}
POST /api/platform/ingredient-proposals/{proposal_id}/map-existing
POST /api/platform/ingredient-proposals/{proposal_id}/add-alias
POST /api/platform/ingredient-proposals/{proposal_id}/approve-new
POST /api/platform/ingredient-proposals/{proposal_id}/reject
POST /api/platform/ingredient-proposals/{proposal_id}/request-information
POST /api/platform/ingredient-proposals/{proposal_id}/mark-duplicate
POST /api/ingredient-proposals/{proposal_id}/provide-information
```

`mark-duplicate` is the explicit platform action for `resolution_status=duplicate`.
`provide-information` lets the submitter return a `needs_information` proposal to `pending`.
`reject`, `request-information`, and `mark-duplicate` require a non-empty `review_note` so submitters always see why the status changed and what to do next.

## Future Evidence Trail And AI Triage

Rejected and duplicate proposals are immutable review history, not permanent name bans. A later proposal with better evidence may be submitted and reviewed independently.

Future proposal workflows should preserve enough evidence for AI-assisted triage and fast platform review:

- original proposed name, locale, description, and culinary context;
- possible existing ingredient and alias matches;
- platform review notes and resolution reason;
- submitter clarification after `needs_information`;
- duplicate/rejection context where it helps future reviewers;
- suggested taxonomy family or signal that a new family may be needed.

The future LLM moderation assistant may recommend mapping, aliasing, approval, rejection, duplicate handling, clarification questions, or a new-family need. It must not mutate canonical ingredients, aliases, families, units, or conversions without platform-admin confirmation.

## Acceptance Criteria

- Household users can submit a proposal without creating an ingredient.
- Platform admins can resolve a proposal as existing ingredient, alias, new canonical ingredient, rejection, duplicate, or needs information.
- Active recipe ingredients still require approved canonical ingredient IDs.
- Proposal review actions are audited with reviewer, timestamp, outcome, and note.
- Tenant isolation tests prove users cannot read other households' private proposal provenance beyond any deliberately public aggregate.
- Taxonomy validation still governs new canonical ingredient approval.

# Recipe Import Drafts

## Document metadata

- **Purpose:** Draft-first recipe import and AI-assisted authoring architecture.
- **Authority:** Feature specification for Phase 16F+; architecture in [ADR 004](../adr/004-draft-first-recipe-authoring-and-external-identifiers.md).
- **Status:** Accepted design — implementation not started.
- **Update when:** Import session states, draft validation, commit semantics, LLM tooling, or serving scaling changes.

---

Recipe import drafts are the staging area between untrusted recipe input and trusted MealRoulette recipes.

Inputs may be manual structured payloads first, then later free text processed by an LLM. In both cases, the output is a draft that must pass deterministic validation and explicit user review before commit.

## Goals

- Persist multi-step recipe authoring sessions.
- Represent unresolved, ambiguous, and missing ingredients without polluting trusted recipe tables.
- Let users review metadata, quantities, steps, timers, and ingredient resolution before commit.
- Provide a deterministic foundation for future LLM-assisted recipe authoring.

## Non-goals

- No LLM provider in the draft foundation phase.
- No URL scraping, OCR, PDF import, or arbitrary web browsing initially.
- No automatic ingredient proposal approval.
- No direct commit while required ingredients remain unresolved.
- No localization generation in the draft foundation phase.

## State Machine

```text
created
  -> extracting
  -> structured
  -> resolving_ingredients
      -> needs_user_resolution
      -> needs_ingredient_proposal
      -> resolved
  -> validating
      -> needs_correction
      -> ready_to_commit
  -> committed

Any non-terminal state:
  -> cancelled
  -> failed
```

## Activation Invariant

A draft may commit to active recipe data only when:

- every required ingredient has an approved canonical `ingredient_id`;
- all units exist;
- quantities are structurally valid;
- steps are ordered;
- timers and temperatures are valid;
- household ownership is correct;
- no unresolved proposal remains for required ingredients;
- the user explicitly confirms the commit.

## Data Model

```text
recipe_import_sessions
- id UUID
- household_id
- created_by_user_id
- status
- source_type
    free_text
    pasted_recipe
    structured_json
    url          # later
    image_ocr    # later
- source_locale
- source_text NULL
- provider NULL
- model NULL
- prompt_version NULL
- schema_version
- raw_model_response_json NULL
- created_dish_id NULL
- created_recipe_id NULL
- created_at
- updated_at

recipe_drafts
- id UUID
- import_session_id
- proposed_dish_name
- proposed_variant_name
- description NULL
- reference_servings
- serving_description NULL
- prep_time_minutes NULL
- cook_time_minutes NULL
- difficulty NULL
- recipe_type NULL
- source_url NULL
- draft_json
- validation_status
- validation_errors_json
- revision

recipe_draft_ingredients
- id UUID
- recipe_draft_id
- sequence_number
- source_text
- quantity_value NUMERIC NULL
- quantity_max NUMERIC NULL
- unit_id NULL
- preparation_note NULL
- scaling_rule
    linear
    rounded_count
    to_taste
    fixed
- resolution_status
    resolved
    ambiguous
    missing
    ignored
- resolved_ingredient_id NULL
- ingredient_proposal_id NULL
- candidate_matches_json
- confidence NULL

recipe_draft_steps
- id UUID
- recipe_draft_id
- step_number
- instruction
- duration_seconds NULL
- duration_seconds_max NULL
- timer_seconds NULL
- timer_label NULL
- timer_optional BOOLEAN
- temperature_value NULL
- temperature_unit NULL
- appliance_metadata_json NULL
```

## Serving Scaling

Recipes keep reference quantities. Scaling is contextual.

```text
scaling_factor = requested_servings / reference_servings
```

`meal_plan_items.servings_planned` should be added when planning needs a serving count different from the recipe reference.

Default ingredient scaling is `linear`. Other rules:

- `rounded_count`: exact value remains available; display/shopping may round countable units.
- `to_taste`: show approximate guidance but preserve "adjust to taste".
- `fixed`: do not scale.

Cooking times are not multiplied automatically. Display a warning when quantities are scaled and timings remain reference timings.

## Timers

Steps may have both operation duration and timer suggestion:

- `duration_seconds`: how long the operation takes;
- `timer_seconds`: whether cooking mode should offer a timer;
- `timer_optional`: whether the timer is suggested rather than required;
- `timer_label`: localized later through translation fields.

Do not infer timers at cooking time if the recipe already has structured timer metadata.

## Validation

Blocking deterministic errors:

- missing required canonical ingredient;
- unknown unit;
- invalid quantity;
- duplicate or missing step numbers;
- invalid timer or temperature;
- missing household ownership;
- unresolved required proposal.

Non-blocking deterministic warnings:

- ingredient not mentioned in steps;
- step mentions an ingredient absent from ingredient list;
- step durations conflict with declared cooking time;
- bake/roast instruction lacks temperature;
- likely useful timer absent.

Future AI quality warnings must be labeled separately from deterministic validation.

## LLM Integration Boundary

LLM-assisted authoring is a later phase. It may populate or revise drafts, but cannot commit trusted data.

Provider calls must return schema-constrained structured output and store:

- provider;
- model;
- prompt version;
- schema version;
- token usage;
- latency;
- raw response;
- parsed result;
- validation result.

## API Sketch

```text
POST   /api/recipe-imports
GET    /api/recipe-imports/{import_id}
POST   /api/recipe-imports/{import_id}/extract
POST   /api/recipe-imports/{import_id}/resolve-ingredients
POST   /api/recipe-imports/{import_id}/validate
POST   /api/recipe-imports/{import_id}/commit
DELETE /api/recipe-imports/{import_id}

PATCH  /api/recipe-imports/{import_id}/draft
PATCH  /api/recipe-imports/{import_id}/ingredients/{draft_ingredient_id}
PATCH  /api/recipe-imports/{import_id}/steps/{step_id}
```

## Acceptance Criteria

- A draft can be created, edited, validated, cancelled, and committed without any LLM provider.
- A draft with unresolved required ingredients cannot commit.
- Ingredient proposals may be linked from missing draft ingredients.
- Commit creates household-owned dish/recipe/ingredient/step rows only after explicit confirmation.
- Shopping and planning never read uncommitted draft rows.
- Serving scaling is represented as reference quantity plus contextual factor, not duplicated recipes.

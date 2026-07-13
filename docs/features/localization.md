# MealRoulette — Localization & Translation

## Document metadata

- **Purpose:** Multilingual content and UI chrome design (Phase 12).
- **Authority:** Canonical for localization design; not yet implemented in product.
- **Status:** Living design — implementation deferred to Phase 12.
- **Update when:** Localization architecture or approval workflow changes.

---

This document is the design spec for multilingual **content** (dishes, recipes, ingredients) and how it relates to multilingual **UI chrome** (buttons, labels).

Product principles (same as LLM-assisted entry elsewhere):

- **LLM suggests once** → stored as draft → **human approves** → deterministic forever.
- **No live translation** on page load or shopping-list generation.
- **Bulk jobs** are idempotent, auditable, and field-aware.

See also: [SPECS.md](../../SPECS.md), [CURSOR_ROADMAP.md](../CURSOR_ROADMAP.md) Phase 11.

---

## Two separate language systems

| System | What | Where | Example |
| --- | --- | --- | --- |
| **UI language** | App chrome | Frontend (`react-i18next` or similar) | Save, Shopping list, Add ingredient |
| **Content language** | User/domain data | Database translation layer | `dish.name`, `recipe_step.instruction`, `ingredient.display_name` |

Do not mix them. Recipes can be French while code and admin tooling stay English.

---

## Source language (`default_locale`)

Not all catalog content is English. Each translatable entity should record its **source locale**:

| Entity | Field | Example |
| --- | --- | --- |
| `dishes` | `default_locale` | `en`, `fr`, `ca` |
| `recipes` | `default_locale` | inherits from dish if unset |
| `ingredients` | `default_locale` | `en` for seed; `fr` if created from French recipes |

Translation jobs use **source locale → target locale**. Never assume source is English.

The **source field value** on the entity remains the canonical text in `default_locale` until explicitly migrated.

---

## What is translatable vs stable

### Translate (via `translations` table)

| Entity | Fields | Notes |
| --- | --- | --- |
| Dish | `name`, `description`, `notes` | Short natural food names |
| Recipe | `variant_name`, `description`, `notes` | Variant labels |
| Recipe step | `instruction` | Imperative; preserve numbers/units (see below) |
| Ingredient | `display_name`, `notes` | Grocery-store terms |
| Ingredient conversion | `notes` (basis) | e.g. "one medium carrot" |
| Recipe ingredient | `notes` | Optional line notes |
| Tag | `label` | Key stays `family:name` |
| Unit | `label` | Symbol stays `g`, `ml`, `unit` |

### Do not translate

- `canonical_name` (ingredient slug: `carrot`, `cherry_tomato`)
- Tag keys (`protein:fish`, `style:soup`)
- Enum values (`prefer_count`, `draft`, `active`)
- Unit symbols (`g`, `kg`, `ml`, `tsp`, `unit`, `clove`)
- Conversion factors
- Internal IDs and API keys

---

## Ingredient aliases ≠ translations

| Concept | Purpose | Storage |
| --- | --- | --- |
| **Display translation** | What the user sees in locale FR | `translations` (`entity_type=ingredient`, `field_name=display_name`, `locale=fr`) |
| **Search alias** | Normalize recipe/import input | `ingredient_aliases` (`alias`, `language`) |

Example for carrot:

- Translation: `display_name` → **Carotte** (shown in UI)
- Aliases: `carotte`, `carottes`, `carrot`, `carrots`, `zanahoria` (matching only)

After a bulk FR translation job, an **optional second pass** may LLM-suggest new FR aliases → stored as draft aliases → admin approves in the ingredient dashboard.

---

## `translations` table

```text
translations
  id
  entity_type          # dish | recipe | recipe_step | ingredient | tag | unit | ...
  entity_id
  field_name           # name | description | instruction | display_name | label | notes
  locale               # fr | en | ca | fr-FR (store BCP-47; match base locale in fallback)
  text
  source_locale        # locale of source text at generation time
  source_text_hash     # sha256 of normalized source text
  source               # manual | llm | imported
  status               # draft | approved | stale | rejected
  reviewed_by_user_id  # nullable FK users
  reviewed_at          # nullable timestamptz
  created_at
  updated_at

UNIQUE (entity_type, entity_id, field_name, locale)
```

### Status lifecycle

| Status | Meaning | Visible to normal users? |
| --- | --- | --- |
| `draft` | LLM or import; not reviewed | No |
| `approved` | Reviewed and current | Yes |
| `stale` | Source text changed after approval | No (fall back to source) |
| `rejected` | Admin rejected; keep for audit | No |

### Staleness detection

On every write to a translatable source field:

1. Compute `new_hash = sha256(normalize(source_text))`.
2. For each translation row for `(entity, field)`:
   - If `source_text_hash != new_hash` and `status == approved` → set `status = stale`.
   - Draft/rejected unchanged unless admin triggers regenerate.

### Idempotent bulk job

| Situation | Action |
| --- | --- |
| No row | Create `draft` |
| `approved` + hash match | Skip |
| `approved` + hash mismatch | Mark `stale`; optionally queue new `draft` |
| `draft` | Update text + hash (or prompt admin) |
| `rejected` | Skip unless admin requests regenerate |

---

## Locale fallback

```text
get_localized(entity, field, requested_locale):
  1. approved translation for exact locale (e.g. fr-FR)
  2. approved translation for base locale (fr)
  3. entity.default_locale source field
  4. raw source field on entity (last resort)
```

Never return `draft` or `stale` translations to non-admin API consumers.

---

## Bulk localization jobs

```text
localization_jobs
  id
  target_locale
  source_locale              # optional; default per-entity default_locale
  status                     # pending | running | completed | failed | cancelled
  total_fields
  translated_fields
  skipped_fields
  failed_fields
  created_by_user_id
  created_at
  finished_at
  error_message

localization_job_items
  id
  job_id
  entity_type
  entity_id
  field_name
  status                     # pending | done | skipped | failed
  error_message
```

### One-click flow (admin)

1. Admin clicks **Generate French translations**.
2. Backend finds translatable fields missing **approved** target translation (or stale).
3. Exclude empty source fields.
4. Compute `source_text_hash` per field.
5. Batch by `entity_type` + `field_name` for field-aware prompts.
6. Send batches to LLM with glossary (below).
7. Store results as `status=draft`, `source=llm`.
8. Optionally suggest ingredient aliases for target locale (separate alias draft flow).
9. Admin reviews side-by-side; approve → `approved` + `reviewed_by` / `reviewed_at`.
10. Future source edits mark translations `stale`.

---

## Glossary & protected terms

Culinary and brand terms must not be blind-translated.

Maintain a project glossary (YAML seed and/or DB table):

```yaml
protected_terms:
  - Thermomix
  - TM6
  - allioli
  - fideua
  - shakshuka
  - dukkah
  - halloumi

glossary:
  scallion:
    fr: cébette
    ca: ceba tendra
  zucchini:
    fr: courgette
    ca: carbassó
  eggplant:
    fr: aubergine
    ca: albergínia
```

Passed into every LLM translation prompt. Dish names that are proper nouns may be listed under `protected_terms`.

---

## Field-aware LLM instructions

| Field | Instruction emphasis |
| --- | --- |
| `dish.name` | Short, natural food name |
| `dish.description` | Natural prose |
| `recipe.variant_name` | Short variant label |
| `recipe_step.instruction` | Imperative cooking step |
| `ingredient.display_name` | Grocery-store term |
| `conversion.notes` | Short factual basis |
| `notes` | Preserve tone and detail |

### Recipe steps — hard constraints

Prompt must require preserving unchanged:

- Quantities and numbers
- Times and durations
- Temperatures
- Unit symbols (`g`, `ml`, `°C`)
- Speeds and appliance settings (Thermomix speed, reverse blade, etc.)
- Step order

---

## Unit labels & shopping display

- **Symbols** (`g`, `ml`) — never translated.
- **Labels** (`gram`, `gramme`, `pièce`) — via `translations` on `unit.label` or equivalent.
- **Ingredient-aware count display** (future): `2 carottes` vs `2 pièces` — presentation layer on top of internal `2 unit`; not a substitute for translations.

---

## Implementation phases

| Phase | When | Scope |
| --- | --- | --- |
| **A — Foundation** | Phase 11 (with LLM infra) | Migration: `translations`, `localization_jobs`, `default_locale` on dish/recipe/ingredient; `get_localized()`; staleness on write |
| **B — Review UI** | Phase 11 | Admin side-by-side review; approve/reject; tag & unit labels |
| **C — Bulk LLM job** | Phase 11 | Field-aware batched translate + glossary; optional alias suggestions |
| **D — UI locale** | Phase 11–12 | User locale preference; `react-i18next` for chrome only |

### Not now (Phase 6 / v0.3)

- Finish shopping lists, ingredient seed import, ingredient dashboard.
- French content via **aliases** and French recipe text in source fields is enough until Phase 11.
- No `translations` table migration until there is a consumer (locale-aware API + review UI).

### Optional early prep (low cost, only if needed before Phase 11)

- Add `default_locale` column with default `'en'` in a migration when touching catalog schema anyway.
- Do **not** build LLM jobs or review UI until Phase 11.

---

## API sketch (Phase 11)

```text
GET  /api/dishes?locale=fr
GET  /api/recipes/{id}?locale=fr
POST /api/admin/localization/jobs          { target_locale, source_locale? }
GET  /api/admin/localization/jobs/{id}
GET  /api/admin/translations?status=draft&locale=fr
PUT  /api/admin/translations/{id}          { status, text? }
```

All admin localization endpoints require `admin` role.

---

## Related existing patterns

| Feature | Pattern |
| --- | --- |
| Ingredient unit conversions | `approved`, `source`, admin review |
| Ingredient seed YAML | `review_status: draft_needs_human_review` |
| LLM roadmap | Draft-only; never silent persist |

Localization reuses the same trust model.

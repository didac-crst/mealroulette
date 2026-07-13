# Taxonomy Validation Workflow

## Document metadata

- **Purpose:** Deterministic + LLM + human exception review for ingredient batches.
- **Authority:** Working spec for validation tooling — not product behaviour.
- **Status:** Working spec.
- **Update when:** Validation commands or promotion workflow change.

---

## Purpose

Support a broad ingredient expansion, potentially around 2,000 candidate ingredients, without requiring
the human owner to review every row manually.

The intended workflow is:

```text
flat candidate list -> deterministic validation -> LLM semantic validation -> exception report -> human reviews exceptions -> promote accepted rows
```

## Review Tiers

Rows should end up in one of these states:

```text
auto_accepted
llm_reviewed
needs_human_review
blocked
promoted
deprecated
```

Human review should focus only on exceptions:

- alias collisions
- ambiguous names
- suspicious conversions
- low-confidence LLM classification
- new families
- ingredients used in existing recipes
- ingredients that materially affect scheduler traits

The human should not need to inspect all 2,000 rows.

## Auto-Accept Criteria

A candidate can be auto-accepted only if all of these are true:

- required fields are present
- `canonical_name` can be generated uniquely
- food group exists
- family exists
- family belongs to the same food group
- aliases are unique after normalization
- no alias collides with an existing active ingredient
- no risk flags are present
- no unit conversions are proposed, or all proposed conversions are low-risk and unapproved
- LLM semantic review agrees with food group and family at high confidence
- close duplicate check is clean

If any condition fails, the row is not auto-accepted.

## Deterministic Validation

Implement a validator command:

```bash
python -m mealroulette.commands.validate_taxonomy \
  --taxonomy backend/mealroulette/data/taxonomy \
  --candidates backend/mealroulette/data/taxonomy/candidate_ingredients_backlog.yaml \
  --report /tmp/taxonomy_validation_report.md \
  --json-report /tmp/taxonomy_validation_report.json
```

The command should check:

- duplicate food group IDs
- duplicate family IDs
- duplicate canonical ingredient names
- invalid family food group references
- invalid ingredient food group references
- invalid ingredient family references
- family/ingredient food group mismatch
- duplicate aliases after normalization
- ambiguous aliases shared by multiple active ingredients
- invalid unit symbols
- non-positive conversion factors
- conversion confidence/source values
- unapproved conversion count
- missing descriptions
- missing aliases for high-priority candidates
- missing family for non-pantry ingredients
- ingredients in `other` food group
- ingredients in `pantry` food group when a semantic food group exists
- pantry flag suspicious for major food groups

## Alias Normalization

Use one normalization function for validation and resolver indexing:

- lowercase
- trim
- remove accents
- normalize ligatures such as `œ -> oe`
- convert `_` and punctuation to spaces
- collapse spaces
- preserve meaningful tokens

Examples:

```text
"Cœur de bœuf" -> "coeur de boeuf"
"pimentón ahumado" -> "pimenton ahumado"
"cherry_tomato" -> "cherry tomato"
```

## Risk Flags

Use risk flags to force review without blocking the whole batch:

```text
ambiguous_name
alias_collision
requires_split
new_family
new_food_group
conversion_suspicious
conversion_high_impact
pantry_flag_suspicious
food_group_mismatch
family_mismatch
regional_name_ambiguous
used_in_existing_recipe
trait_high_impact
shopping_high_impact
```

## Conversion Policy

Conversions are riskier than names and descriptions because they affect shopping totals and vectors.

Default policy:

```text
generated approximate conversions -> approved: false
reviewed household-standard conversions -> approved: true
exact unit conversions -> approved: true
```

Classification policy:

```text
food_group describes what the ingredient is
storage_class / pantry_item describes storage and background behavior
```

Flag rows such as canned tomatoes, passata, canned tuna, dry pasta, or preserved peppers if they use:

```yaml
food_group: pantry
```

They should instead use their semantic group, for example:

```yaml
food_group: vegetable
storage_class: pantry
pantry_item: true
```

`food_group: pantry` is acceptable only as a reviewed fallback for non-food/background cooking agents that do not fit another group, such as some leavening or processing agents.

Examples that can be approved if already known:

- `unit egg -> 55 g`
- `can canned_tomatoes -> 400 g`

Examples that should usually remain unapproved:

- `ml rice -> g`
- `tbsp spice -> g`
- `unit vegetable -> g` when size varies heavily

## LLM Semantic Validation

LLM should review batches but not rewrite the YAML directly.

Output should be structured findings:

```json
{
  "findings": [
    {
      "severity": "review",
      "ingredient": "cream",
      "field": "canonical identity",
      "issue": "Ingredient is too broad and can mean several dairy products.",
      "recommended_change": "Split into heavy_cream, single_cream, creme_fraiche, sour_cream, and cream_cheese as needed.",
      "rationale": "Alias resolution would be ambiguous."
    }
  ]
}
```

Severity values:

```text
blocker
review
suggestion
accepted
```

## Exception Report

The validator should produce a human-readable report:

```markdown
# Taxonomy Validation Report

## Summary

- Candidates: 2,000
- Auto-accepted: 1,420
- LLM-reviewed: 360
- Needs human review: 200
- Blocked: 20

## Blockers

...

## Needs Human Review

...

## Alias Collisions

...

## Suspicious Conversions

...

## New Families Proposed

...
```

The human owner reviews the report, not the full catalog.

## Promotion Workflow

Promotion from candidate backlog to canonical taxonomy should:

1. Generate `canonical_name`.
2. Assign `display_name`.
3. Confirm food group.
4. Confirm family.
5. Add description.
6. Add aliases.
7. Add units.
8. Add conversions as unapproved unless deterministic or reviewed.
9. Mark review status.
10. Write to `ingredients_seed.yaml`.

Do not promote `blocked` rows.

Rows with `needs_human_review` must stay out of active resolver output unless explicitly allowed.

## Batch Strategy

Generate broad candidate lists first, then promote in batches.

Recommended first large candidate batches:

1. France and Spain core produce
2. France and Spain meat/fish/seafood
3. France and Spain dairy/cheese
4. Mediterranean pantry and herbs
5. Asian-Europe staples
6. Mexican-Europe staples
7. Middle Eastern and North African staples
8. Alias cleanup and duplicate review

## Cursor Implementation Notes

Build this as tooling, not as a one-off script:

- reusable loader
- reusable validator
- reusable normalization
- JSON + Markdown reports
- unit tests for duplicate alias detection and food group/family validation

Do not require the full 2,000-row catalog to finish Phase 9. The infrastructure and first reviewed batches are enough.

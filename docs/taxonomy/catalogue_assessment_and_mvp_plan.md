# Catalogue Assessment And MVP Expansion Plan

## Overall Assessment

The taxonomy structure is promising, but 2,000 canonical ingredients is too many for the first active release.

Current proposal status before this improvement pass:

- 312 candidate ingredients
- 73 ingredient families
- 22 food groups
- about 210 candidates
- about 102 rows marked `needs_human_review`
- two empty families: `mushroom_family` and `asian_mushroom_family`

The high-level food groups are broad enough for the app. The family layer is useful for similarity and substitution, but several families need tightening before further expansion.

Recommended catalogue stages:

| Stage | Canonical ingredients | Purpose |
| --- | ---: | --- |
| MVP | 500-700 | Most ordinary French, Spanish, and European household recipes |
| Strong European release | 900-1,200 | Regional dishes and common international recipes |
| Mature catalogue | 1,500-2,000 | Specialist ingredients, cuts, varieties, and prepared products |

The critical metric is not ingredient count. It is:

```text
What percentage of supported recipes can be represented without arbitrary free-text ingredients?
```

A clean catalogue of 700 ingredients is more useful than 2,000 entries with unnecessary varieties, duplicated prepared products, and fragmented shopping aggregation.

## Recommendation

Do not manually invent 1,700 more active entries now.

Instead:

1. Fix classification and unit model.
2. Add about 250 obvious missing essentials.
3. Import or create the first 300-500 actual recipes.
4. Record unresolved ingredient names during recipe ingestion.
5. Promote frequently recurring unresolved names into canonical ingredients.
6. Keep rare product names as aliases or recipe-local text until they justify canonical status.

## Target MVP Distribution

| Area | Previous rough count | Suggested MVP |
| --- | ---: | ---: |
| Vegetables and mushrooms | 55 | 95 |
| Fruit | 17 | 40 |
| Starches, bread, and baking | 42 | 85 |
| Meat and charcuterie | 32 | 65 |
| Fish and seafood | 29 | 50 |
| Dairy, eggs, and cheese | 31 | 60 |
| Legumes and plant protein | 14 | 30 |
| Herbs and spices | 27 | 65 |
| Oils, condiments, and sauces | 38 | 85 |
| Nuts, seeds, and sweeteners | 16 | 35 |
| Stocks, alcohol, and other pantry | 11 | 40 |

## Structural Fixes Before Expansion

### Food Group vs Storage

Do not use `pantry` as the semantic food group for tomato products, canned fish, dry pasta, spices, or preserved vegetables.

Use:

```yaml
food_group: vegetable
storage_class: pantry
pantry_item: true
```

instead of:

```yaml
food_group: pantry
family: tomato_family
```

`pantry_item` and `storage_class` describe storage/shopping/background behavior. `food_group` describes what the ingredient is.

### Product State

Create separate canonical ingredients only when product state materially affects:

- recipe compatibility
- shopping location
- unit conversion
- shelf life
- substitution

Good separate entries:

- fresh cod vs salt cod
- fresh anchovies vs anchovy fillets in oil
- fresh salmon vs smoked salmon
- canned tuna vs fresh tuna

Avoid mechanical explosions:

- dry chickpeas
- canned chickpeas
- jarred chickpeas
- cooked chickpeas
- frozen chickpeas

Prefer structured modifiers later:

```text
state: dried | cooked | fresh
preservation: canned | jarred | frozen | none
```

### Default Units

Default units should match natural cooking and shopping language.

Examples:

```yaml
egg:
  default_recipe_unit: unit
  preferred_shopping_unit: unit
  aggregation_unit: unit

lemon:
  default_recipe_unit: unit
  preferred_shopping_unit: unit
  aggregation_unit: unit

milk:
  default_recipe_unit: ml
  preferred_shopping_unit: ml
  aggregation_unit: ml

olive_oil:
  default_recipe_unit: tbsp
  preferred_shopping_unit: ml
  aggregation_unit: ml
```

### Aliases And Locales

Current aliases mix translations, plurals, and synonym resolution.

Short term: keep flat `aliases` for compatibility.

Long term, prefer:

```yaml
translations:
  en:
    name: Tomato
    aliases: [tomatoes]
  fr:
    name: Tomate
    aliases: [tomates]
  es:
    name: Tomate
    aliases: [tomates]
  ca:
    name: Tomàquet
    aliases: [tomàquets]
```

Do not block Phase 9 on multilingual restructuring, but keep descriptions and aliases ready for it.

## Highest Priority Missing Areas

1. Mushrooms and Asian mushrooms.
2. Common French/Spanish vegetables.
3. Bread, flour, starch, yeast, and baking basics.
4. Balanced raw meat cuts across chicken, beef, veal, lamb, turkey.
5. Fresh/smoked/salted/canned fish distinctions where meaningful.
6. Dairy variants, eggs, egg yolks, egg whites.
7. Generic cheese concepts before every protected cheese.
8. Legumes and canned/cooked pulse policy.
9. French/Spanish herbs and aromatics.
10. Foundational spices including salt and pepper.
11. Oils, fats, vinegars, and basic cooking agents.
12. French/Spanish condiments and preserved products.
13. Europe-common Asian, Mexican, Middle Eastern, and North African staples.

## Empty Family Fixes

Populate these immediately:

- `mushroom_family`
- `asian_mushroom_family`

Essential European mushrooms:

- button mushroom
- brown button mushroom
- portobello
- oyster mushroom
- porcini
- dried porcini
- chanterelle
- morel
- black trumpet
- mixed wild mushrooms
- truffle
- truffle paste

Common Asian mushrooms in Europe:

- shiitake
- dried shiitake
- enoki
- king oyster mushroom
- shimeji
- wood ear mushroom
